'''Cobra protocol.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import base64
import itertools
import json
import logging
import platform
from typing import Dict
from urllib.parse import parse_qs, urlparse

import ujson
import websockets

from cobras.common.apps_config import generateNonce
from cobras.common.auth_hash import computeHash
from cobras.common.cobra_types import JsonDict
from cobras.common.task_cleanup import addTaskCleanup
from cobras.common.throttle import Throttle
from cobras.common.version import getVersion
from cobras.server.connection_state import ConnectionState
from cobras.server.redis_connections import RedisConnections
from cobras.server.redis_kv_store import kvStoreRead
from cobras.server.redis_subscriber import (
    RedisSubscriberMessageHandlerClass,
    redisSubscriber,
    validatePosition,
)
from cobras.server.stream_sql import InvalidStreamSQLError, StreamSqlFilter


async def respond(state: ConnectionState, ws, app: Dict, data: JsonDict):
    response = json.dumps(data)
    logging.info(f"> {response}")

    try:
        await ws.send(response)
    except websockets.exceptions.ConnectionClosed as e:
        logging.warning(f'Trying to write in a closed connection: {e}')


async def handleAuth(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    try:
        secret = app['apps_config'].getRoleSecret(state.appkey, state.role)
    except KeyError:
        reason = 'invalid_role'
        success = False
    else:
        serverHash = computeHash(secret, state.nonce.encode('ascii'))
        clientHash = pdu.get('body', {}).get('credentials', {}).get('hash')

        state.log(f'server hash {serverHash}')
        state.log(f'client hash {clientHash}')

        success = clientHash == serverHash
        if not success:
            reason = 'challenge_failed'

    if success:
        response = {
            "action": "auth/authenticate/ok",
            "id": pdu.get('id', 1),
            "body": {},
        }

        state.authenticated = True
        state.permissions = app['apps_config'].getPermissions(state.appkey, state.role)
    else:
        logging.warning(f'auth error: {reason}')
        response = {
            "action": "auth/authenticate/error",
            "id": pdu.get('id', 1),
            "body": {"error": "authentication_failed", "reason": reason},
        }
    await respond(state, ws, app, response)


async def badFormat(state: ConnectionState, ws, app: Dict, reason: str):
    response = {"body": {"error": "bad_schema", "reason": reason}}
    state.ok = False
    state.error = response
    await respond(state, ws, app, response)


def parseAppKey(path):
    '''
    Parse url
    path = /v2?appkey=FFFFFFFFFFFFEEEEEEEEEEEEE
    '''
    parseResult = urlparse(path)
    args = parse_qs(parseResult.query)
    appkey = args.get('appkey')
    if appkey is None or not isinstance(appkey, list) or len(appkey) != 1:
        return None

    appkey = appkey[0]
    return appkey


async def handleHandshake(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    authMethod = pdu.get('body', {}).get('method')
    if authMethod != 'role_secret':
        errMsg = f'invalid auth method: {authMethod}'
        logging.warning(errMsg)
        response = {
            "action": f"auth/handshake/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    role = pdu.get('body', {}).get('data', {}).get('role')
    state.role = role
    state.nonce = generateNonce()

    response = {
        "action": "auth/handshake/ok",
        "id": pdu.get('id', 1),
        "body": {
            "data": {
                "nonce": state.nonce,
                "version": getVersion(),
                "connection_id": state.connection_id,
                "node": platform.uname().node,
            }
        },
    }
    await respond(state, ws, app, response)


async def handlePublish(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    '''Here we don't write back a result to the client for efficiency.
    Client doesn't really needs it.
    '''
    # Use plugins to transform input data, if any
    plugins = app.get('plugins')
    if plugins is not None:
        pdu = plugins.updateMsg(state.appkey, pdu)

    # Missing message
    message = pdu.get('body', {}).get('message')
    if message is None:
        errMsg = 'publish: empty message'
        logging.warning(errMsg)
        response = {
            "action": "rtm/publish/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Missing channels
    channel = pdu.get('body', {}).get('channel')
    channels = pdu.get('body', {}).get('channels')
    if channel is None and channels is None:
        errMsg = 'publish: no channel or channels field'
        logging.warning(errMsg)
        response = {
            "action": "rtm/publish/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    if channels is None:
        channels = [channel]

    batchPublish = app['apps_config'].isBatchPublishEnabled(state.appkey)

    # We could have metrics per channel
    for chan in channels:
        appkey = state.appkey

        try:
            pipelinedPublisher = await app['pipelined_publishers'].get(appkey, chan)

            await pipelinedPublisher.push((appkey, chan, serializedPdu), batchPublish)
        except Exception as e:
            errMsg = f'publish: cannot connect to redis {e}'
            logging.warning(errMsg)
            response = {
                "action": "rtm/publish/error",
                "id": pdu.get('id', 1),
                "body": {"error": errMsg},
            }
            await respond(state, ws, app, response)
            return

    response = {"action": "rtm/publish/ok", "id": pdu.get('id', 1), "body": {}}
    await respond(state, ws, app, response)

    # Stats
    app['stats'].updatePublished(state.role, len(serializedPdu))


async def handleSubscribe(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    '''
    Client doesn't really needs it.
    '''
    body = pdu.get('body', {})
    channel = body.get('channel')

    subscriptionId = body.get('subscription_id')

    if channel is None and subscriptionId is None:
        errMsg = 'missing channel and subscription_id'
        logging.warning(errMsg)
        response = {
            "action": "rtm/subscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    maxSubs = app['max_subscriptions']
    if maxSubs >= 0 and len(state.subscriptions) + 1 > maxSubs:
        errMsg = f'subscriptions count over max limit: {maxSubs}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/subscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        state.ok = False
        state.error = response
        await respond(state, ws, app, response)
        return

    if channel is None:
        channel = subscriptionId

    if subscriptionId is None:
        subscriptionId = channel

    filterStr = body.get('filter')
    hasFilter = filterStr not in ('', None)

    try:
        streamSQLFilter = StreamSqlFilter(filterStr) if hasFilter else None
    except InvalidStreamSQLError:
        errMsg = f'Invalid SQL expression {filterStr}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/subscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        state.ok = False
        state.error = response
        await respond(state, ws, app, response)
        return

    if hasFilter:
        channel = streamSQLFilter.channel

    position = body.get('position')
    if not validatePosition(position):
        errMsg = f'Invalid position: {position}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/subscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        state.ok = False
        state.error = response
        await respond(state, ws, app, response)
        return

    response = {
        "action": "rtm/subscribe/ok",
        "id": pdu.get('id', 1),
        "body": {
            "position": "1519190184:559034812775",
            "subscription_id": subscriptionId,
        },
    }

    class MessageHandlerClass(RedisSubscriberMessageHandlerClass):
        def __init__(self, args):
            self.cnt = 0
            self.cntPerSec = 0
            self.throttle = Throttle(seconds=1)
            self.ws = args['ws']
            self.subscriptionId = args['subscription_id']
            self.hasFilter = args['has_filter']
            self.streamSQLFilter = args['stream_sql_filter']
            self.appkey = args['appkey']
            self.serverStats = args['stats']
            self.state = args['state']
            self.subscribeResponse = args['subscribe_response']
            self.app = args['app']
            self.idIterator = itertools.count()

        def log(self, msg):
            self.state.log(msg)

        async def on_init(self, redisConnection):
            response = self.subscribeResponse
            if redisConnection is None:
                response['body']['action'] = 'rtm/subscribe/error'
            else:
                response['body']['redis_node'] = redisConnection.host
            await respond(self.state, self.ws, self.app, response)

        async def handleMsg(self, msg: dict, position: str, payloadSize: int) -> bool:

            # Input msg is the full serialized publish pdu.
            # Extract the real message out of it.
            msg = msg.get('body', {}).get('message')

            self.serverStats.updateSubscribed(self.state.role, payloadSize)

            if self.hasFilter:
                filterOutput = self.streamSQLFilter.match(
                    msg.get('messages') or msg
                )  # noqa
                if not filterOutput:
                    return True
                else:
                    msg = filterOutput

            pdu = {
                "action": "rtm/subscription/data",
                "id": next(self.idIterator),
                "body": {
                    "subscription_id": self.subscriptionId,
                    "messages": [msg],
                    "position": position,
                },
            }
            self.state.log(f"> {json.dumps(pdu)} at position {position}")

            await self.ws.send(json.dumps(pdu))

            self.cnt += 1
            self.cntPerSec += 1

            if self.throttle.exceedRate():
                return True

            self.state.log(f"#messages {self.cnt} msg/s {self.cntPerSec}")
            self.cntPerSec = 0

            return True

    appChannel = '{}::{}'.format(state.appkey, channel)

    redisConnections = RedisConnections(app['redis_urls'], app['redis_password'])

    task = asyncio.create_task(
        redisSubscriber(
            redisConnections,
            appChannel,
            position,
            MessageHandlerClass,
            {
                'ws': ws,
                'subscription_id': subscriptionId,
                'has_filter': hasFilter,
                'stream_sql_filter': streamSQLFilter,
                'appkey': state.appkey,
                'stats': app['stats'],
                'state': state,
                'subscribe_response': response,
                'app': app,
            },
        )
    )
    addTaskCleanup(task)

    key = subscriptionId + state.connection_id
    state.subscriptions[key] = (task, state.role)

    app['stats'].incrSubscriptions(state.role)


async def handleUnSubscribe(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    '''
    Cancel a subscription
    '''
    body = pdu.get('body', {})

    subscriptionId = body.get('subscription_id')
    if subscriptionId is None:
        errMsg = f'Body Missing subscriptionId'
        logging.warning(errMsg)
        response = {
            "action": "rtm/unsubscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    key = subscriptionId + state.connection_id
    item = state.subscriptions.get(key, (None, None))
    task, _ = item
    if task is None:
        errMsg = f'Invalid subscriptionId: {subscriptionId}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/unsubscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Correct path
    response = {"action": "rtm/unsubscribe/ok", "id": pdu.get('id', 1)}
    await respond(state, ws, app, response)

    task.cancel()


#
# Admin operations
#
async def handleAdminGetConnections(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    action = pdu['action']
    connections = list(app['connections'].keys())

    response = {
        "action": f"{action}/ok",
        "id": pdu.get('id', 1),
        "body": {'connections': connections},
    }
    await respond(state, ws, app, response)


async def handleAdminCloseConnection(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    action = pdu['action']
    body = pdu.get('body', {})
    targetConnectionId = body.get('connection_id')

    if targetConnectionId is None:
        errMsg = f'Missing connection id'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    found = False
    for connectionId, (state, websocket) in app['connections'].items():
        if connectionId == targetConnectionId:
            targetWebSocket = websocket
            found = True

    if not found:
        errMsg = f'Cannot find connection id'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    await targetWebSocket.close()

    response = {"action": f"{action}/ok", "id": pdu.get('id', 1), "body": {}}
    await respond(state, ws, app, response)


# FIXME
async def toggleFileLogging(state: ConnectionState, app: Dict, params: JsonDict):
    found = False
    for connectionId, (st, websocket) in app['connections'].items():
        if connectionId == params.get('connection_id', ''):
            st.fileLogging = not st.fileLogging
            found = True

    return {'found': found, 'params': params}


# FIXME (should close current connection)
async def handleAdminCloseAllConnection(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    action = pdu['action']

    websocketLists = []
    for connectionId, (state, websocket) in app['connections'].items():
        if connectionId != state.connection_id:
            websocketLists.append(websocket)

    for ws in websocketLists:
        await ws.close()  # should this be shielded ?

    response = {"action": f"{action}/ok", "id": pdu.get('id', 1), "body": {}}
    await respond(state, ws, app, response)


async def closeAll(state: ConnectionState, app: Dict, params: JsonDict):
    websocketLists = []
    for connectionId, (state, websocket) in app['connections'].items():
        if connectionId != state.connection_id:
            websocketLists.append(websocket)

    for ws in websocketLists:
        await ws.close()  # should this be shielded ?

    return {'status': 'ok'}  # FIXME: return bool


# FIXME error handling
async def handleRead(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):

    body = pdu.get('body', {})
    position = body.get('position')
    channel = body.get('channel')

    appChannel = '{}::{}'.format(state.appkey, channel)

    redisConnections = RedisConnections(app['redis_urls'], app['redis_password'])

    try:
        message = await kvStoreRead(redisConnections, appChannel, position, state.log)
    except Exception as e:
        errMsg = f'write: cannot connect to redis {e}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/read/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Correct path
    response = {
        "action": "rtm/read/ok",
        "id": pdu.get('id', 1),
        "body": {"message": message},
    }
    await respond(state, ws, app, response)


async def handleWrite(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    # Missing message
    message = pdu.get('body', {}).get('message')
    if message is None:
        errMsg = 'write: empty message'
        logging.warning(errMsg)
        response = {
            "action": "rtm/write/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Missing channel
    channel = pdu.get('body', {}).get('channel')
    if channel is None:
        errMsg = 'write: missing channel field'
        logging.warning(errMsg)
        response = {
            "action": "rtm/write/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Extract the message. This is what will be published
    message = pdu['body']['message']

    appkey = state.appkey

    try:
        pipelinedPublisher = await app['pipelined_publishers'].get(appkey, channel)

        await pipelinedPublisher.publishNow(
            (appkey, channel, json.dumps(message)), maxLen=1
        )
    except Exception as e:
        errMsg = f'write: cannot connect to redis {e}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/write/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Stats
    app['stats'].updateWrites(state.role, len(serializedPdu))

    response = {"action": f"rtm/write/ok", "id": pdu.get('id', 1), "body": {}}
    await respond(state, ws, app, response)


def validatePermissions(permissions, action):
    group, sep, verb = action.partition('/')

    if group == 'admin':
        return 'admin' in permissions

    if group == 'auth':
        return True

    # FIXME: ugly that unsubscribe is the only rtm action that does not have
    # its own permission
    if verb == 'unsubscribe':
        return True

    return verb in permissions


AUTH_PREFIX = 'auth'
ACTION_HANDLERS_LUT = {
    f'{AUTH_PREFIX}/handshake': handleHandshake,
    f'{AUTH_PREFIX}/authenticate': handleAuth,
    'rtm/publish': handlePublish,
    'rtm/subscribe': handleSubscribe,
    'rtm/unsubscribe': handleUnSubscribe,
    'rtm/read': handleRead,
    'rtm/write': handleWrite,
    'admin/close_connection': handleAdminCloseConnection,
    'admin/get_connections': handleAdminGetConnections,
}


async def processCobraMessage(state: ConnectionState, ws, app: Dict, msg: bytes):
    try:
        pdu: JsonDict = ujson.loads(msg)
    except ValueError:
        msgEncoded = base64.b64encode(msg)
        errMsg = f'malformed json pdu: base64: {msgEncoded} raw: {msg}'
        await badFormat(state, ws, app, errMsg)
        return

    state.log(f"< {msg}")

    action = pdu.get('action')
    if action is None:
        await badFormat(state, ws, app, f'missing action')
        return

    handler = ACTION_HANDLERS_LUT.get(action)
    if handler is None:
        await badFormat(state, ws, app, f'invalid action: {action}')
        return

    # Make sure the user is authenticated
    if not state.authenticated and not action.startswith(AUTH_PREFIX):
        errMsg = f'action "{action}" needs authentication'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # Make sure the user has permission to access given endpoint
    if not validatePermissions(state.permissions, action):
        errMsg = f'action "{action}": permission denied'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await respond(state, ws, app, response)
        return

    # proceed with handling action
    await handler(state, ws, app, pdu, msg)

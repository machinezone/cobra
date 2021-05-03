'''Pubsub handlers

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import itertools
import json
import logging
from typing import Dict

from cobras.common.channel_builder import updateMsg
from cobras.common.cobra_types import JsonDict
from cobras.common.task_cleanup import addTaskCleanup
from cobras.common.throttle import Throttle
from cobras.server.connection_state import ConnectionState
from rcc.subscriber import (
    RedisSubscriberMessageHandlerClass,
    redisSubscriber,
    validatePosition,
)
from cobras.server.stream_sql import InvalidStreamSQLError, StreamSqlFilter


async def handlePublish(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: str
):
    '''Here we don't write back a result to the client for efficiency.
    Client doesn't really needs it.
    '''
    # Potentially add extra channels with channel builder rules
    rules = app['apps_config'].getChannelBuilderRules(state.appkey)
    pdu = updateMsg(rules, pdu)

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
        await state.respond(ws, response)
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
        await state.respond(ws, response)
        return

    if channels is None:
        channels = [channel]

    streams = {}

    appkey = state.appkey
    redis = app['redis_clients'].getRedisClient(appkey)

    for chan in channels:

        # sanity check to skip empty channels
        if chan is None:
            continue

        try:
            maxLen = app['channel_max_length']
            stream = '{}::{}'.format(appkey, chan)
            streamId = await redis.xadd(stream, 'json', serializedPdu, maxLen)

            streams[chan] = streamId
        except Exception as e:
            # await publishers.erasePublisher(appkey, chan)  # FIXME

            errMsg = f'publish: cannot connect to redis {e}'
            logging.warning(errMsg)
            response = {
                "action": "rtm/publish/error",
                "id": pdu.get('id', 1),
                "body": {"error": errMsg},
            }
            await state.respond(ws, response)
            return

        app['stats'].updateChannelPublished(chan, len(serializedPdu))

    response = {
        "action": "rtm/publish/ok",
        "id": pdu.get('id', 1),
        "body": {'channels': channels},
    }
    await state.respond(ws, response)

    # Stats
    app['stats'].updatePublished(state.role, len(serializedPdu))


async def handleSubscribe(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: str
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
        await state.respond(ws, response)
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
        await state.respond(ws, response)
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
        state.error = response
        await state.respond(ws, response)
        return

    if hasFilter and streamSQLFilter is not None:
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
        await state.respond(ws, response)
        return

    batchSize = body.get('batch_size', 1)
    try:
        batchSize = int(batchSize)
    except ValueError:
        errMsg = f'Invalid batch size: {batchSize}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/subscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        state.ok = False
        state.error = response
        await state.respond(ws, response)
        return

    response = {
        "action": "rtm/subscribe/ok",
        "id": pdu.get('id', 1),
        "body": {
            # FIXME: we should set the position by querying
            # the redis stream, inside the MessageHandler
            "position": "1519190184-559034812775",
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
            self.channel = args['channel']
            self.batchSize = args['batch_size']
            self.idIterator = itertools.count()

            self.messages = []

        def log(self, msg):
            self.state.log(msg)

        async def on_init(self, initInfo):
            response = self.subscribeResponse
            response['body'].update(initInfo)

            if not initInfo.get('success', False):
                msgId = response['id']
                response = {
                    'action': 'rtm/subscribe/error',
                    'id': msgId,
                    'body': {
                        'error': 'subscribe error: server cannot connect to redis'
                    },
                }

            # Send response.
            await self.state.respond(self.ws, response)

        async def handleMsg(self, msg: dict, position: str, payloadSize: int) -> bool:

            # Input msg is the full serialized publish pdu.
            # Extract the real message out of it.
            msg = msg.get('body', {}).get('message')

            self.serverStats.updateSubscribed(self.state.role, payloadSize)
            self.serverStats.updateChannelSubscribed(self.channel, payloadSize)

            if self.hasFilter:
                filterOutput = self.streamSQLFilter.match(
                    msg.get('messages') or msg
                )  # noqa
                if not filterOutput:
                    return True
                else:
                    msg = filterOutput

            self.messages.append(msg)
            if len(self.messages) < self.batchSize:
                return True

            assert position is not None

            pdu = {
                "action": "rtm/subscription/data",
                "id": next(self.idIterator),
                "body": {
                    "subscription_id": self.subscriptionId,
                    "messages": self.messages,
                    "position": position,
                },
            }
            serializedPdu = json.dumps(pdu)
            self.state.log(f"> {serializedPdu} at position {position}")

            await self.ws.send(serializedPdu)

            self.cnt += len(self.messages)
            self.cntPerSec += len(self.messages)

            self.messages = []

            if self.throttle.exceedRate():
                return True

            self.state.log(f"#messages {self.cnt} msg/s {self.cntPerSec}")
            self.cntPerSec = 0

            return True

    appChannel = '{}::{}'.format(state.appkey, channel)

    # We need to create a new connection as reading from it will be blocking
    redisClient = app['redis_clients'].makeRedisClient()

    task = asyncio.ensure_future(
        redisSubscriber(
            redisClient.redis,
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
                'channel': channel,
                'batch_size': batchSize,
            },
        )
    )
    addTaskCleanup(task)

    key = subscriptionId + state.connection_id
    state.subscriptions[key] = (task, state.role)

    app['stats'].incrSubscriptions(state.role)


async def handleUnSubscribe(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: str
):
    '''
    Cancel a subscription
    '''
    body = pdu.get('body', {})

    subscriptionId = body.get('subscription_id')
    if subscriptionId is None:
        errMsg = 'Body Missing subscriptionId'
        logging.warning(errMsg)
        response = {
            "action": "rtm/unsubscribe/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await state.respond(ws, response)
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
        await state.respond(ws, response)
        return

    # Correct path
    response = {"action": "rtm/unsubscribe/ok", "id": pdu.get('id', 1)}
    await state.respond(ws, response)

    task.cancel()

'''Key Value store operations (set, get, delete),
but that are using streams for storage

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.

FIXME: missing delete
'''

import asyncio
import json
import logging
from typing import Dict, Optional

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState
from cobras.server.redis_connections import RedisConnections


async def kvStoreRead(
    redisConnections: RedisConnections, pattern: str, position: Optional[str], logger
):
    # Create connection
    connection = await redisConnections.create(pattern)

    if position is None:
        # Get the last entry written to a stream
        end = '-'
        start = '+'
    else:
        start = position
        end = start

    try:
        results = await connection.xrevrange(pattern, start, end, 1)
        if not results:
            return None

        result = results[0]
        position = result[0]
        msg = result[1]
        data = msg[b'json']

        msg = json.loads(data)
        return msg

    except asyncio.CancelledError:
        logger('Cancelling redis subscription')
        raise

    finally:
        # When finished, close the connection.
        connection.close()


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
        await state.respond(ws, response)
        return

    # Correct path
    response = {
        "action": "rtm/read/ok",
        "id": pdu.get('id', 1),
        "body": {"message": message},
    }
    await state.respond(ws, response)


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
        await state.respond(ws, response)
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
        await state.respond(ws, response)
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
        await state.respond(ws, response)
        return

    # Stats
    app['stats'].updateWrites(state.role, len(serializedPdu))

    response = {"action": f"rtm/write/ok", "id": pdu.get('id', 1), "body": {}}
    await state.respond(ws, response)


async def handleDelete(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: bytes
):
    # Missing channel
    channel = pdu.get('body', {}).get('channel')
    if channel is None:
        errMsg = 'delete: missing channel field'
        logging.warning(errMsg)
        response = {
            "action": "rtm/delete/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await state.respond(ws, response)
        return

    appChannel = '{}::{}'.format(state.appkey, channel)

    try:
        redisConnections = RedisConnections(app['redis_urls'], app['redis_password'])
        redisConnection = await redisConnections.create(appChannel)
        await redisConnection.delete(appChannel)
    except Exception as e:
        errMsg = f'delete: cannot connect to redis {e}'
        logging.warning(errMsg)
        response = {
            "action": "rtm/delete/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await state.respond(ws, response)
        return

    # Stats
    app['stats'].updateWrites(state.role, len(serializedPdu))

    response = {"action": f"rtm/delete/ok", "id": pdu.get('id', 1), "body": {}}
    await state.respond(ws, response)

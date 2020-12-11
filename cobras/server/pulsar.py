'''Pulsar protocol.

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.

TODO:
* Handle consumer acks
* Support message reader
'''

import asyncio
import base64
import json
import logging
from typing import Dict

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState


async def badFormat(state: ConnectionState, ws, app: Dict, reason: str):
    response = {"result": "error", "reason": reason}
    state.ok = False
    state.error = response
    await state.respond(ws, response)


async def handleProducerMessage(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: str, path: str
):
    tokens = path.split('/')
    if len(tokens) != 8:
        await badFormat(state, ws, app, f'Invalid uri -> {path}')
        return

    tenant = tokens[5]
    namespace = tokens[6]
    # FIXME: topic can contain multiple /
    topic = tokens[7]

    chan = f'{tenant}::{namespace}::{topic}'
    payload = pdu.get('payload')  # FIXME error if missing
    context = pdu.get('context')  # FIXME error if missing ??

    args = ['payload', payload, 'context', context]

    appkey = state.appkey
    redis = app['redis_clients'].getRedisClient(appkey)

    try:
        maxLen = app['channel_max_length']
        stream = '{}::{}'.format(appkey, chan)
        streamId = await redis.xaddRaw(stream, maxLen, *args)
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

    response = {"result": "ok", "messageId": streamId.decode(), "context": context}
    await state.respond(ws, response)


async def handleConsumerMessage(state: ConnectionState, ws, app: Dict, path: str):
    tokens = path.split('/')
    if len(tokens) != 9:
        await badFormat(state, ws, app, f'Invalid uri -> {path}')
        return

    tenant = tokens[5]
    namespace = tokens[6]
    # FIXME: topic can contain multiple /
    topic = tokens[7]

    chan = f'{tenant}::{namespace}::{topic}'

    redis = app['redis_clients'].makeRedisClient()

    while True:
        try:
            stream = '{}::{}'.format(state.appkey, chan)
            messages = await redis.xread(stream, '$')

            messages = messages[stream.encode()]

            for message in messages:
                streamId = message[0].decode()
                body = message[1]

                response = {}
                response["payload"] = body[b'payload'].decode()
                response["messageId"] = streamId

                if b'context' in response:
                    response["context"] = body[b'context'].decode()

                await state.respond(ws, response)

                # await a response to ack the message, and delete it
                await ws.recv()

                # FIXME: stats message received
                # app['stats'].updateChannelPublished(chan, len(serializedPdu))

        except asyncio.CancelledError:
            logging.info('Cancelling redis subscription')
            raise

        except Exception as e:
            errMsg = f'Exception {e}'
            await badFormat(state, ws, app, errMsg)
            return


async def processPulsarMessage(state: ConnectionState, ws, app: Dict, path: str):
    try:
        state.role = path.split('/')[3]
    except Exception:
        await badFormat(state, ws, app, f'Invalid endpoint: {path}')
        return

    if path.startswith('/ws/v2/producer'):
        async for serializedPdu in ws:
            state.msgCount += 1
            try:
                pdu: JsonDict = json.loads(serializedPdu)
            except json.JSONDecodeError:
                msgEncoded = base64.b64encode(serializedPdu.encode()).decode()
                errMsg = f'malformed json pdu for agent "{ws.userAgent}" '
                errMsg += f'base64: {msgEncoded} raw: {serializedPdu}'
                await badFormat(state, ws, app, errMsg)
                return

            state.log(f"< {serializedPdu}")

            await handleProducerMessage(state, ws, app, pdu, serializedPdu, path)
    elif path.startswith('/ws/v2/consumer'):
        state.role = 'consumer'
        await handleConsumerMessage(state, ws, app, path)
    else:
        await badFormat(state, ws, app, f'Invalid endpoint: {path}')

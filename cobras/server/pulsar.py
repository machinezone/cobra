'''Pulsar protocol.

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

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


async def handlePublishMessage(
    state: ConnectionState, ws, app: Dict, pdu: JsonDict, serializedPdu: str, path: str
):
    tokens = path.split('/')
    if len(tokens) != 8:
        await badFormat(state, ws, app, f'Invalid uri -> {path}')
        return

    tenant = tokens[5]
    namespace = tokens[6]
    topic = tokens[7]

    chan = f'{tenant}::{namespace}::{topic}'
    payload = pdu.get('payload')
    context = pdu.get('context')

    appkey = state.appkey
    redis = app['redis_clients'].getRedisClient(appkey)

    try:
        maxLen = app['channel_max_length']
        stream = '{}::{}'.format(appkey, chan)
        streamId = await redis.xadd(stream, 'json', payload, maxLen)
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


async def processPulsarMessage(
    state: ConnectionState, ws, app: Dict, serializedPdu: str, path: str
):
    try:
        pdu: JsonDict = json.loads(serializedPdu)
    except json.JSONDecodeError:
        msgEncoded = base64.b64encode(serializedPdu.encode()).decode()
        errMsg = f'malformed json pdu for agent "{ws.userAgent}" '
        errMsg += f'base64: {msgEncoded} raw: {serializedPdu}'
        await badFormat(state, ws, app, errMsg)
        return

    state.log(f"< {serializedPdu}")

    if path.startswith('/ws/v2/producer'):
        await handlePublishMessage(state, ws, app, pdu, serializedPdu, path)
    else:
        await badFormat(state, ws, app, f'Invalid endpoint: {path}')

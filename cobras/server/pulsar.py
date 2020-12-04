'''Pulsar protocol.

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

import base64
import json
from typing import Dict

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState


async def badFormat(state: ConnectionState, ws, app: Dict, reason: str):
    response = {"body": {"error": "bad_schema", "reason": reason}}
    state.ok = False
    state.error = response
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

    # Fake happy response
    response = {
        "action": f"youpi",
        "id": pdu.get('id', 1),
        "body": {"error": "ooooooo"},
    }
    await state.respond(ws, response)
    return

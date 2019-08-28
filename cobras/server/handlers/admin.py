'''Admin handlers. Admin tasks are not expected to be ran commonly by apps

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import logging
from typing import Dict

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState


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
    await state.respond(ws, response)


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
        await state.respond(ws, response)
        return

    found = False
    for connectionId, (_, websocket) in app['connections'].items():
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
        await state.respond(ws, response)
        return

    await targetWebSocket.close()

    response = {"action": f"{action}/ok", "id": pdu.get('id', 1), "body": {}}
    await state.respond(ws, response)


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
    for connectionId, (st, websocket) in app['connections'].items():
        if connectionId != st.connection_id:
            websocketLists.append(websocket)

    for websocket in websocketLists:
        await websocket.close()  # should this be shielded ?

    response = {"action": f"{action}/ok", "id": pdu.get('id', 1), "body": {}}
    await state.respond(ws, response)


async def closeAll(state: ConnectionState, app: Dict, params: JsonDict):
    websocketLists = []
    for connectionId, (state, websocket) in app['connections'].items():
        if connectionId != state.connection_id:
            websocketLists.append(websocket)

    for ws in websocketLists:
        await ws.close()  # should this be shielded ?

    return {'status': 'ok'}  # FIXME: return bool

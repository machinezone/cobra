'''Cobra protocol.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import base64
import rapidjson as json
import logging
from typing import Dict

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState
from cobras.server.handlers.admin import (
    handleAdminCloseConnection,
    handleAdminGetConnections,
)
from cobras.server.handlers.auth import handleAuth, handleHandshake
from cobras.server.handlers.kv_store import handleDelete, handleRead, handleWrite
from cobras.server.handlers.pubsub import (
    handlePublish,
    handleSubscribe,
    handleUnSubscribe,
)


async def badFormat(state: ConnectionState, ws, app: Dict, reason: str):
    response = {"body": {"error": "bad_schema", "reason": reason}}
    state.ok = False
    state.error = response
    await state.respond(ws, response)


def validatePermissions(permissions, action):
    group, _, verb = action.partition('/')

    if group == 'admin':
        return 'admin' in permissions

    if group == 'auth':
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
    'rtm/delete': handleDelete,
    'admin/close_connection': handleAdminCloseConnection,
    'admin/get_connections': handleAdminGetConnections,
}


async def processCobraMessage(state: ConnectionState, ws, app: Dict, msg: bytes):

    try:
        pdu: JsonDict = json.loads(msg)
    except json.JSONDecodeError:
        msgEncoded = base64.b64encode(msg.encode())
        errMsg = f'malformed json pdu: base64: {msgEncoded} raw: {msg}'
        errMsg += f' / agent "{ws.userAgent}"'
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
        errMsg = f'action "{action}" needs authentication / agent "{ws.userAgent}"'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await state.respond(ws, response)
        return

    # Make sure the user has permission to access given endpoint
    if not validatePermissions(state.permissions, action):
        errMsg = f'action "{action}": permission denied / agent "{ws.userAgent}"'
        logging.warning(errMsg)
        response = {
            "action": f"{action}/error",
            "id": pdu.get('id', 1),
            "body": {"error": errMsg},
        }
        await state.respond(ws, response)
        return

    # proceed with handling action
    await handler(state, ws, app, pdu, msg)

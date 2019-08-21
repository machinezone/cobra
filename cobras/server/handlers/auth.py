'''Authentication handler (2 steps)

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import platform
import logging
from typing import Dict

from cobras.common.cobra_types import JsonDict
from cobras.server.connection_state import ConnectionState
from cobras.common.apps_config import generateNonce
from cobras.common.auth_hash import computeHash
from cobras.common.version import getVersion


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
        await state.respond(ws, response)
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
    await state.respond(ws, response)


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
    await state.respond(ws, response)

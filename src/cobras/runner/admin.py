'''Publish to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import functools
import json

import click
import uvloop

from cobras.client.client import client
from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                      getDefaultSecretForApp)
from cobras.common.apps_config import ADMIN_APPKEY
from cobras.common.superuser import preventRootUsage

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={ADMIN_APPKEY}'


async def clientCallback(websocket, **args):
    method = args['method']
    params = args.get('params')
    params = json.loads(params)

    pdu = {
        "action": "rpc/admin",
        "id": 1,
        "body": {
            "method": method,
            "params": params
        }
    }

    await websocket.send(json.dumps(pdu))

    response = await websocket.recv()
    print(response)


async def start(url, credentials, verbose, method, params):
    callback = functools.partial(clientCallback,
                                 verbose=verbose,
                                 method=method,
                                 params=params)

    task = asyncio.create_task(
        client(url, credentials, callback))
    await task


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('admin'))
@click.option('--secret', default=getDefaultSecretForApp('admin'))
@click.option('--verbose', is_flag=True)
@click.option('--method', default='close_all')
@click.option('--params', default='{}')
def admin(url, role, secret, verbose, method, params):
    '''Admin

    \b
    cobra admin --method toggle_file_logging --params '{"connection_id": ".."}'
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(role, secret)

    asyncio.get_event_loop().run_until_complete(start(url, credentials,
                                                      verbose, method, params))

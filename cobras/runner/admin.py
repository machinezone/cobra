'''Publish to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging

import click
from cobras.client.connection import Connection
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.common.apps_config import ADMIN_APPKEY, getDefaultPort

DEFAULT_URL = f'ws://127.0.0.1:{getDefaultPort()}/v2?appkey={ADMIN_APPKEY}'


async def adminCoroutine(url, creds, action, connectionId):

    connection = Connection(url, creds)
    try:
        await connection.connect()
    except Exception as e:
        logging.error(f'Error connecting: {e}')
        return

    if action == 'get_connections':
        openedConnections = await connection.adminGetConnections()
        print(f'#{len(openedConnections)} connection(s)')
        for connection in openedConnections:
            print(f'\t{connection}')

    elif action == 'disconnect':
        await connection.adminCloseConnection(connectionId)


@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('admin'))
@click.option('--secret', default=getDefaultSecretForApp('admin'))
@click.option('--action', default='get_connections')
@click.option('--connection_id')
@click.command()
def admin(url, role, secret, action, connection_id):
    '''Execute admin operations on the server

    \b
    cobra admin --action disconnect --connection_id 3919dc67
    '''

    credentials = createCredentials(role, secret)

    asyncio.get_event_loop().run_until_complete(
        adminCoroutine(url, credentials, action, connection_id)
    )

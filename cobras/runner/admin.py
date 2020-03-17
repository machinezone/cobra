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
from cobras.common.apps_config import ADMIN_APPKEY, getDefaultEndpoint, makeUrl


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


@click.option('--endpoint', default=getDefaultEndpoint())
@click.option('--appkey', default=ADMIN_APPKEY)
@click.option('--rolename', default=getDefaultRoleForApp('admin'))
@click.option('--rolesecret', default=getDefaultSecretForApp('admin'))
@click.option('--action', default='get_connections')
@click.option('--connection_id')
@click.command()
def admin(endpoint, appkey, rolename, rolesecret, action, connection_id):
    '''Execute admin operations on the server

    \b
    cobra admin --action disconnect --connection_id 3919dc67
    '''

    url = makeUrl(endpoint, appkey)
    credentials = createCredentials(rolename, rolesecret)

    asyncio.get_event_loop().run_until_complete(
        adminCoroutine(url, credentials, action, connection_id)
    )

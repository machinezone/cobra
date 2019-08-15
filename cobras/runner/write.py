'''Write to the cobra key value store

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio

import click
import uvloop

# from cobras.client.kv_store import readClient
from cobras.client.connection import Connection
from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                       getDefaultSecretForApp)
from cobras.common.apps_config import PUBSUB_APPKEY
from cobras.common.superuser import preventRootUsage

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={PUBSUB_APPKEY}'


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('pubsub'))
@click.option('--secret', default=getDefaultSecretForApp('pubsub'))
@click.option('--channel', default='sms_republished_v1_neo')
@click.option('--data', default='{"foo": "bar"}')
def write(url, role, secret, channel, data):
    '''Write to the cobra key value store
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(role, secret)

    async def handler(url, credentials, channel, data):
        connection = Connection(url, credentials, verbose=True)
        await connection.connect()
        await connection.write(channel, data)
        await connection.close()

    asyncio.get_event_loop().run_until_complete(handler(url, credentials, channel, data))


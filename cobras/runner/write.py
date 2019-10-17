'''Write to the cobra key value store

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging

import click

# from cobras.client.kv_store import readClient
from cobras.client.connection import ActionException, Connection
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.common.apps_config import PUBSUB_APPKEY, getDefaultPort

DEFAULT_URL = f'ws://127.0.0.1:{getDefaultPort()}/v2?appkey={PUBSUB_APPKEY}'


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('pubsub'))
@click.option('--secret', default=getDefaultSecretForApp('pubsub'))
@click.option('--channel', default='sms_republished_v1_neo_kv_store')
@click.option('--data', default='{"foo": "bar"}')
@click.option('--repeat', is_flag=True)
def write(url, role, secret, channel, data, repeat):
    '''Write to the cobra key value store
    '''
    credentials = createCredentials(role, secret)

    async def handler(url, credentials, channel, data, repeat):
        connection = Connection(url, credentials)
        await connection.connect()

        try:
            while True:
                await connection.write(channel, data)
                if not repeat:
                    break
        except ActionException as e:
            logging.error(f'Action error: {e}')
            return

        await connection.close()

    asyncio.get_event_loop().run_until_complete(
        handler(url, credentials, channel, data, repeat)
    )

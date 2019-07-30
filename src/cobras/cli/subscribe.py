'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import json

import click
import uvloop

from cobras.client.client import subscribeClient
from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                      getDefaultSecretForApp)
from cobras.common.apps_config import PUBSUB_APPKEY
from cobras.common.throttle import Throttle
from cobras.common.superuser import preventRootUsage

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={PUBSUB_APPKEY}'


class MessageHandlerClass:
    def __init__(self, websockets, args):
        self.cnt = 0
        self.cntPerSec = 0
        self.throttle = Throttle(seconds=1)
        self.verbose = args['verbose']

    async def on_init(self):
        pass

    async def handleMsg(self, msg: str) -> bool:
        self.cnt += 1
        self.cntPerSec += 1

        if self.verbose >= 1:
            data = json.loads(msg)
            print(data['body']['messages'][0])

        if self.throttle.exceedRate():
            return True

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return True


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('pubsub'))
@click.option('--secret', default=getDefaultSecretForApp('pubsub'))
@click.option('--channel', default='sms_republished_v1_neo')
@click.option('--verbose', '-v', count=True)
@click.option('--stream_sql')
def subscribe(url, role, secret, channel, stream_sql, verbose):
    '''Subscribe to a channel
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(role, secret)

    asyncio.get_event_loop().run_until_complete(
            subscribeClient(url, credentials, channel,
                            stream_sql, MessageHandlerClass,
                            {'verbose': verbose}))

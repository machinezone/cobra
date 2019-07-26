'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import json

import click
import uvloop

from cobra.client.client import subscribeClient
from cobra.client.credentials import createCredentials
from cobra.common.apps_config import PUBSUB_APPKEY
from cobra.common.throttle import Throttle
from cobra.runner.superuser import preventRootUsage

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
@click.option('--channel', default='sms_republished_v1_neo')
@click.option('--verbose', '-v', count=True)
@click.option('--stream_sql')
@click.pass_obj
def subscribe(auth, url, channel, stream_sql, verbose):
    '''Subscribe to a channel
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(auth.role, auth.secret)

    asyncio.get_event_loop().run_until_complete(
            subscribeClient(url, credentials, channel,
                            stream_sql, MessageHandlerClass,
                            {'verbose': verbose}))

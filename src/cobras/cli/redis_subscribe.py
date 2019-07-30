'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
import uvloop

from cobras.common.throttle import Throttle
from cobras.common.superuser import preventRootUsage
from cobras.server.redis_connections import RedisConnections
from cobras.server.subscribe import runSubscriber


class MessageHandlerClass:
    def __init__(self, obj):
        self.cnt = 0
        self.cntPerSec = 0
        self.throttle = Throttle(seconds=1)

    def log(self, msg):
        print(msg)

    async def on_init(self, redisConnection):
        pass

    async def handleMsg(self, msg: str, payloadSize: int) -> bool:
        self.cnt += 1
        self.cntPerSec += 1

        if self.throttle.exceedRate():
            return True

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return True


@click.command()
@click.option('--redis_urls', default='redis://localhost')
@click.option('--redis_password')
@click.option('--channel')
@click.option('--appkey')
def redis_subscribe(redis_urls, redis_password, channel, appkey):
    '''Subscribe to a channel

    \b
    cobra subscribe --redis_urls redis://localhost:7379 --channel foo --appkey bar  # noqa

    \b
    cobra subscribe --redis_urls redis://redis:6379 --channel foo --appkey bar
    [From a bench container]

    \b
    cobra subscribe --redis_urls 'redis://localhost:7001;redis://localhost:7002' --channel foo --appkey bar  # noqa
    '''

    preventRootUsage()
    uvloop.install()

    appChannel = '{}::{}'.format(appkey, channel)
    redisConnections = RedisConnections(redis_urls, redis_password)
    runSubscriber(redisConnections, appChannel, MessageHandlerClass)

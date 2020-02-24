'''Subscribe to a channel (with XREAD)

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import click
from rcc.client import RedisClient
from rcc.subscriber import RedisSubscriberMessageHandlerClass, runSubscriber
from datetime import datetime, timedelta


class Throttle(object):
    def __init__(self, seconds: int = 1, minutes: int = 0, hours: int = 0) -> None:
        self.throttle_period = timedelta(seconds=seconds, minutes=minutes, hours=hours)
        self.time_of_last_call = datetime.min

    def exceedRate(self) -> bool:
        now = datetime.now()
        time_since_last_call = now - self.time_of_last_call

        if time_since_last_call > self.throttle_period:
            self.time_of_last_call = now
            return False
        else:
            return True


class MessageHandlerClass(RedisSubscriberMessageHandlerClass):
    def __init__(self, obj):
        self.cnt = 0
        self.cntPerSec = 0

        self.throttle = Throttle(seconds=1)

    def log(self, msg):
        print(msg)

    async def on_init(self, redisClient, streamExists, streamLength):
        if redisClient is None:
            print('Failure connecting to redis')
        else:
            print(f'stream exists: {streamExists} stream length: {streamLength}')

    async def handleMsg(self, msg: str, position: str, payloadSize: int) -> bool:
        self.cnt += 1
        self.cntPerSec += 1

        if self.throttle.exceedRate():
            return True

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return True


@click.command()
@click.option('--redis_url', default='redis://localhost')
@click.option('--redis_password')
@click.option('--channel', default='foo')
@click.option('--position')
def subscribe(redis_url, redis_password, channel, position):
    '''Subscribe to a channel

    \b
    rcc subscribe --redis_url redis://localhost:7379 --channel foo
    '''

    redisClient = RedisClient(redis_url, redis_password)
    runSubscriber(redisClient, channel, position, MessageHandlerClass)

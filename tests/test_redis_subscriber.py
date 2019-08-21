'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

# FIXME: this test does nothing !!!

import asyncio
import json
import uuid

from cobras.common.task_cleanup import addTaskCleanup
from cobras.server.pipelined_publisher import PipelinedPublisher
from cobras.server.redis_connections import RedisConnections
from cobras.server.redis_subscriber import (
    RedisSubscriberMessageHandlerClass,
    redisSubscriber,
)


async def subscribeCoroutine():
    '''Starts a server, then run a health check'''

    redisUrls = 'redis://localhost'
    redisPassword = None
    redisConnections = RedisConnections(redisUrls, redisPassword)

    db = await redisConnections.create('default_channel')

    # Start publishing on a random channel
    channel = uuid.uuid4().hex

    class MessageHandlerClass(RedisSubscriberMessageHandlerClass):
        def __init__(self, obj):
            self.cnt = 0
            self.cntPerSec = 0
            self.channel = obj['channel']
            self.redis = obj['redis']

            self.message = json.dumps({'hello': 'world'})

        def log(self, msg):
            print(msg)

        async def on_init(self):
            print('Publishing message to a redis channel')
            self.redis.publish(self.channel, self.message)
            await self.redis.execute()

        async def handleMsg(self, msg: str, position: str, payloadSize: int) -> bool:
            print(f'Received message from redis at position {position}')
            message = json.dumps(msg)
            assert message == self.message
            print('Expected message received')

            return False

    task = asyncio.create_task(
        redisSubscriber(
            redisConnections,
            channel,
            None,
            MessageHandlerClass,
            {'redis_urls': redisUrls, 'channel': channel, 'redis': db},
        )
    )
    addTaskCleanup(task)

    # FIXME: needs a timeout
    while True:
        await asyncio.sleep(0.1)
        if task.done():
            break


def test_subscribe():
    asyncio.get_event_loop().run_until_complete(subscribeCoroutine())

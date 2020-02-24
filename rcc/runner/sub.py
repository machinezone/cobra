'''Subscribe to a channel (with PUBSUB)

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import click
from rcc.client import RedisClient


async def subscriber(
    redisClient: RedisClient, channel: str, pattern: str, timeout: int
):
    async def cb(obj, message):
        print('Received', message)
        obj.append(message)

    obj = []
    if pattern:
        task = asyncio.create_task(redisClient.psubscribe(pattern, cb, obj))
    else:
        task = asyncio.create_task(redisClient.subscribe(channel, cb, obj))

    await asyncio.sleep(timeout)

    # Cancel the task
    task.cancel()
    await task

    print()
    print(f'Got {len(obj)} messages')
    for item in obj:
        print(f'Got {item}')


@click.command()
@click.option('--redis_url', default='redis://localhost')
@click.option('--redis_password')
@click.option('--channel', default='foo')
@click.option('--pattern')
@click.option('--timeout', default=360)
def sub(redis_url, redis_password, channel, pattern, timeout):
    '''Subscribe to a channel

    \b
    rcc sub --redis_url redis://localhost:7379 --channel foo
    '''

    redisClient = RedisClient(redis_url, redis_password)

    asyncio.get_event_loop().run_until_complete(
        subscriber(redisClient, channel, pattern, timeout)
    )

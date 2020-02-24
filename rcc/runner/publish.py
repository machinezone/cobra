'''Publish to a channel (with XADD)

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
from urllib.parse import urlparse

import click
from rcc.client import RedisClient


async def pub(redis_url, redis_password, channel, msg, batch, maxLen):
    client = RedisClient(redis_url, redis_password)
    await client.connect()

    if batch:
        while True:
            streamId = await client.send(
                'XADD', channel, 'MAXLEN', '~', maxLen, b'*', 'json', msg
            )
    else:
        streamId = await client.send(
            'XADD', channel, 'MAXLEN', '~', maxLen, b'*', 'json', msg
        )
        print('Stream id:', streamId)


@click.command()
@click.option('--redis_url', default='redis://localhost')
@click.option('--port', '-p')
@click.option('--redis_password')
@click.option('--channel', default='foo')
@click.option('--msg', default='{"bar": "baz"}')
@click.option('--batch', is_flag=True)
@click.option('--max_len', default='100')
def publish(redis_url, port, redis_password, channel, msg, batch, max_len):
    '''Publish to a channel
    '''

    if port is not None:
        netloc = urlparse(redis_url).netloc
        host, _, _ = netloc.partition(':')
        redis_url = f'redis://{host}:{port}'

    asyncio.get_event_loop().run_until_complete(
        pub(redis_url, redis_password, channel, msg, batch, max_len)
    )

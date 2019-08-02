'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio

from cobras.server.redis_publisher import (RedisPublisher,
                                           create_redis_publisher)


async def start():
    # content = 'PING\r\n'
    host = 'localhost'
    port = 6379
    password = 'foobar'
    password = None
    verbose = True
    redis = await create_redis_publisher(host, port, password, verbose)

    for i in range(100):
        redis.publish(b'foo', b'bar')
    results = await redis.execute()
    assert len(results) == 100

    redis.close()
    await redis.wait_closed()


def test_redis():
    asyncio.get_event_loop().run_until_complete(start())

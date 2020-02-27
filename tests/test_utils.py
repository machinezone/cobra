'''Test utilities

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio

from rcc.client import RedisClient


def makeClient(port=None):
    # redis_url = 'redis://localhost:10000'  # for cluster
    redis_url = 'redis://localhost'
    redis_password = None

    if port is not None:
        redis_url += f':{port}'

    client = RedisClient(redis_url, redis_password)
    return client


# Start redis server at a given port
async def runRedisServer(port):
    cmd = f'redis-server --port {port}'

    try:
        proc = await asyncio.create_subprocess_shell(cmd)
        stdout, stderr = await proc.communicate()
    finally:
        proc.terminate()

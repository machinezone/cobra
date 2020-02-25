'''Test utilities

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

from rcc.client import RedisClient


def makeClient(port=None):
    # redis_url = 'redis://localhost:10000'  # for cluster
    redis_url = 'redis://localhost'
    redis_password = None

    if port is not None:
        redis_url += f':{port}'

    client = RedisClient(redis_url, redis_password)
    return client

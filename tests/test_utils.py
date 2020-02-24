'''Test utilities

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import os
import tempfile

from rcc.client import RedisClient
from rcc.cluster.init_cluster import runNewCluster


def makeClient(port=None):
    # redis_url = 'redis://localhost:10000'  # for cluster
    redis_url = 'redis://localhost'
    redis_password = None

    if port is not None:
        redis_url += f':{port}'

    client = RedisClient(redis_url, redis_password)
    return client

'''Handle set of redis connections. Used for sharding connections.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import logging
from urllib.parse import urlparse

import asyncio_redis
from uhashring import HashRing

from cobras.server.redis_publisher import create_redis_publisher


class RedisConnections():
    def __init__(self, urls: str, password) -> None:
        self.urls = urls.split(';')
        self.password = password
        if password == '':
            self.password = None

        # create a consistent hash ring
        # https://www.paperplanes.de/2011/12/9/the-magic-of-consistent-hashing.html
        self.hr = HashRing(nodes=self.urls)

    async def create(self, appChannel=None, useAioRedis=True):
        url = self.hashChannel(appChannel)
        logging.debug(f'Hashing {appChannel} to url -> {url}')

        netloc = urlparse(url).netloc
        host, _, port = netloc.partition(':')
        if port:
            port = int(port)
        else:
            port = 6379

        if useAioRedis:
            redis = await create_redis_publisher(host, port, self.password)
        else:
            redis = \
                await asyncio_redis.Connection.create(host=host, port=port,
                                                      password=self.password)

        return redis

    def hashChannel(self, appChannel: str):
        return self.hr.get_node(appChannel)

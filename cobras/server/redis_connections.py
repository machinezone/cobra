'''Handle set of redis connections. Used for sharding connections.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging
import time
import sys
from urllib.parse import urlparse

import aioredis
from uhashring import HashRing


class RedisConnections:
    def __init__(self, urls: str, password) -> None:
        self.urls = urls.split(';')
        self.password = password
        if password == '':
            self.password = None

        # create a consistent hash ring
        # https://www.paperplanes.de/2011/12/9/the-magic-of-consistent-hashing.html
        self.hr = HashRing(nodes=self.urls)

    async def create(self, appChannel=None):
        url = self.hashChannel(appChannel)
        logging.info(f'Hashing {appChannel} to url -> {url}')

        redis = await self.createFromUrl(url)
        return redis

    async def createFromUrl(self, url: str):
        netloc = urlparse(url).netloc
        host, _, port = netloc.partition(':')
        if port:
            port = int(port)
        else:
            port = 6379

        redis = await aioredis.create_redis(url, password=self.password)
        redis.host = host
        return redis

    def hashChannel(self, appChannel: str):
        return self.hr.get_node(appChannel)

    async def waitForAllConnectionsToBeReady(self, timeout: int):
        start = time.time()

        for url in self.urls:
            sys.stderr.write(f'Checking {url} ')

            while True:
                sys.stderr.write('.')
                sys.stderr.flush()

                try:
                    redis = await self.createFromUrl(url)
                    await redis.ping()
                    redis.close()
                    break
                except Exception:
                    if time.time() - start > timeout:
                        sys.stderr.write('\n')
                        raise

                    waitTime = 0.1
                    await asyncio.sleep(waitTime)
                    timeout -= waitTime

            sys.stderr.write('\n')

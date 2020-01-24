'''Handle set of redis connections. Used for sharding connections.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging
import time
import sys
from urllib.parse import urlparse

import aioredis
import tabulate
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

        self.startup_nodes = []
        for url in self.urls:
            netloc = urlparse(url).netloc
            host, _, port = netloc.partition(':')
            if port:
                port = int(port)
            else:
                port = 6379
            self.startup_nodes.append({'host': host, 'port': port})

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

    async def getRedisInfo(self):
        def chunks(lst, n):
            """Yield successive n-sized chunks from lst."""
            for i in range(0, len(lst), n):
                j = i + n
                yield lst[i:j]

        urls = self.urls
        if self.cluster:
            redis = await self.createFromUrl(self.urls[0])
            nodes = await redis.cluster_nodes()

            urls = []
            for node in nodes:
                host = node['host']
                port = node['port']
                url = f'redis://{host}:{port}'
                urls.append(url)

        urls.sort()

        text = ''
        chunkSize = 2 if self.cluster else 3
        for urlsChunk in chunks(urls, chunkSize):

            s = await self.getRedisInfoForUrls(urlsChunk)
            text += '\n\n' + s

        return text

    async def getRedisInfoForUrls(self, urls):
        entries = []
        headers = ['Metric']
        headers.extend(urls)
        entries.append(headers)

        infos = {}
        metrics = []

        if self.cluster:
            # INFO returns info for all nodes in the clusters with our client
            redis = await self.createFromUrl(urls[0])
            await redis.ping()

            infos = await redis.info()
            for key, value in infos.items():
                metrics = value.keys()
                break
        else:
            for url in urls:
                try:
                    redis = await self.createFromUrl(url)
                    await redis.ping()

                    info = await redis.info()
                    infos[url] = info
                    metrics = info.keys()

                except Exception:
                    pass

        for metric in metrics:
            data = [metric]
            for url in urls:
                if self.cluster:
                    prefixLen = len('redis://')
                    url = url[prefixLen:]

                val = infos.get(url, {}).get(metric, 'na')
                data.append(val)

            entries.append(data)

        return tabulate.tabulate(entries, tablefmt="simple", headers="firstrow")

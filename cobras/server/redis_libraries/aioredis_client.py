'''aioredis redis client

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

import collections
from urllib.parse import urlparse

import aioredis


class RedisClientAioRedis(object):
    def __init__(self, url, password, cluster, library):
        self.url = url
        self.password = password
        self.cluster = cluster
        self.library = library

        netloc = urlparse(url).netloc
        host, _, port = netloc.partition(':')
        if port:
            port = int(port)
        else:
            port = 6379

        self.host = host
        self.connected = False

        self.redis = None

    def __del__(self):
        self.close()

    def close(self):
        self.connected = False
        if self.redis is not None:
            self.redis.close()

    async def connect(self):
        self.redis = await aioredis.create_redis(self.url, password=self.password)
        self.connected = True

    async def ping(self):
        if not self.connected:
            await self.connect()

        return await self.redis.ping()

    async def xadd(self, stream, field, data, maxLen):
        if not self.connected:
            await self.connect()

        return await self.redis.xadd(
            stream, {field: data}, max_len=maxLen, exact_len=False
        )

    async def exists(self, key):
        if not self.connected:
            await self.connect()

        return await self.redis.exists(key)

    async def xread(self, streams):
        if not self.connected:
            await self.connect()

        names = [streamName for streamName in streams.keys()]
        ids = [streamId for streamId in streams.values()]

        result = await self.redis.xread(names, timeout=0, latest_ids=ids)
        return self.transformXReadResponse(result)

    async def delete(self, key):
        if not self.connected:
            await self.connect()

        return await self.redis.delete(key)

    async def xrevrange(self, stream, start, end, count):
        if not self.connected:
            await self.connect()

        return await self.redis.xrevrange(stream, start, end, count)

    def transformXReadResponse(self, response):
        d = collections.defaultdict(list)

        for item in response:
            streamName = item[0]
            streamId = item[1]
            value = item[2]

            d[streamName].append((streamId, value))

        return d

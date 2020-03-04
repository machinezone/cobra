'''Small wrapper around an aredis connection

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

import aredis


class RedisClientAredis(object):
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

        if self.cluster:
            cls = aredis.StrictRedisCluster
            self.redis = cls(
                max_connections=1024, startup_nodes=[{'host': host, 'port': port}]
            )
        else:
            cls = aredis.StrictRedis
            self.redis = aredis.StrictRedis(
                host=host, port=port, password=self.password, max_connections=1024
            )

        self.host = host

    def __del__(self):
        self.close()

    def close(self):
        pass

    async def connect(self):
        pass

    async def ping(self):
        return await self.redis.ping()

    async def xadd(self, stream, field, data, maxLen):
        return await self.redis.xadd(
            stream, {field: data}, max_len=maxLen, approximate=True
        )

    async def exists(self, key):
        return await self.redis.exists(key)

    async def xread(self, streams):
        return await self.redis.xread(count=None, block=0, **streams)

    async def delete(self, key):
        return await self.redis.delete(key)

    async def xrevrange(self, stream, start, end, count):
        return await self.redis.xrevrange(stream, start, end, count)

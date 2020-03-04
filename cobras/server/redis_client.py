'''Small wrapper around an aredis connection

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

import aredis


class RedisClient(object):
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

        if self.library == 'aredis':
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
        elif self.library == 'rcc':
            from rcc.client import RedisClient as RC

            self.redis = RC(self.url, self.password)

        self.host = host

    def close(self):
        pass  # FIXME ?

    async def connect(self):
        pass

    async def exists(self, key):
        if self.library == 'aredis':
            return await self.redis.exists(key)

    async def ping(self):
        if self.library == 'aredis':
            return await self.redis.ping()
        else:
            return await self.redis.send('PING')

    async def delete(self, key):
        if self.library == 'aredis':
            await self.redis.delete(key)
        else:
            assert False, 'not implemented'

    async def xadd(self, stream, field, data, maxLen):
        if self.library == 'aredis':
            return await self.redis.xadd(
                stream, {field: data}, max_len=maxLen, approximate=True
            )
        else:
            return await self.redis.send(
                'XADD', stream, 'MAXLEN', '~', maxLen, b'*', field, data
            )

    async def xread(self, streams):
        if self.library == 'aredis':
            return await self.redis.xread(count=None, block=0, **streams)
        else:
            assert False, 'not implemented'

    async def xrevrange(self, stream, start, end, count):
        if self.library == 'aredis':
            return await self.redis.xrevrange(stream, start, end, count)
        else:
            assert False, 'not implemented'

'''Small wrapper around an aredis connection

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

import aredis

DEFAULT_REDIS_LIBRARY = 'rcc'


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
        elif self.library == 'rcc':
            return await self.redis.send('EXISTS', key)
        else:
            assert False, 'not implemented'

    async def ping(self):
        if self.library == 'aredis':
            return await self.redis.ping()
        elif self.library == 'rcc':
            return await self.redis.send('PING')
        else:
            assert False, 'not implemented'

    async def delete(self, key):
        if self.library == 'aredis':
            await self.redis.delete(key)
        elif self.library == 'rcc':
            await self.redis.send('DEL', key)
        else:
            assert False, 'not implemented'

    async def xadd(self, stream, field, data, maxLen):
        if self.library == 'aredis':
            return await self.redis.xadd(
                stream, {field: data}, max_len=maxLen, approximate=True
            )
        elif self.library == 'rcc':
            return await self.redis.send(
                'XADD', stream, 'MAXLEN', '~', maxLen, b'*', field, data
            )
        else:
            assert False, 'not implemented'

    async def xread(self, streams):
        if self.library == 'aredis':
            return await self.redis.xread(count=None, block=0, **streams)
        elif self.library == 'rcc':

            args = ['XREAD', 'BLOCK', b'0', b'STREAMS']
            for item in streams.items():
                args.append(item[0])
                args.append(item[1])

            result = await self.redis.send(*args)
            return result
        else:
            assert False, 'not implemented'

    async def xrevrange(self, stream, start, end, count):
        if self.library == 'aredis':
            return await self.redis.xrevrange(stream, start, end, count)
        elif self.library == 'rcc':
            return await self.redis.send(
                'XREVRANGE', stream, start, end, b'COUNT', count
            )
        else:
            assert False, 'not implemented'

'''Small wrapper around an aredis connection

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

import aredis

DEFAULT_REDIS_LIBRARY = 'justredis'


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
        elif self.library == 'justredis':
            from cobras.server.justredis import Multiplexer

            self.redis = Multiplexer({'endpoints': (host, port)})
            self.db = self.redis.database()

        self.host = host

    def __del__(self):
        self.close()

    def close(self):
        # FIXME we should call aclose for justredis
        pass

    async def connect(self):
        pass

    async def ping(self):
        if self.library == 'aredis':
            return await self.redis.ping()
        elif self.library == 'rcc':
            return await self.redis.send('PING')
        elif self.library == 'justredis':
            cr = self.db.commandreply
            return await cr(b'PING')
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
        elif self.library == 'justredis':
            cr = self.db.commandreply
            return await cr('XADD', stream, 'MAXLEN', '~', maxLen, b'*', field, data)
        else:
            assert False, 'not implemented'

    async def exists(self, key):
        if self.library == 'aredis':
            return await self.redis.exists(key)
        elif self.library == 'rcc':
            return await self.redis.send('EXISTS', key)
        elif self.library == 'justredis':
            cr = self.db.commandreply
            return await cr(b'EXISTS', key)
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
        elif self.library == 'justredis':
            args = ['XREAD', 'BLOCK', b'0', b'STREAMS']
            for item in streams.items():
                args.append(item[0])
                args.append(item[1])

            cr = self.db.commandreply
            result = await cr(*args)
            return self.transformXReadResponse(result)
        else:
            assert False, 'not implemented'

    async def delete(self, key):
        if self.library == 'aredis':
            await self.redis.delete(key)
        elif self.library == 'rcc':
            await self.redis.send('DEL', key)
        elif self.library == 'justredis':
            cr = self.db.commandreply
            return await cr(b'DEL', key)
        else:
            assert False, 'not implemented'

    async def xrevrange(self, stream, start, end, count):
        if self.library == 'aredis':
            return await self.redis.xrevrange(stream, start, end, count)
        elif self.library == 'rcc':
            return await self.redis.send(
                'XREVRANGE', stream, start, end, b'COUNT', count
            )
        elif self.library == 'justredis':
            cr = self.db.commandreply
            args = ['XREVRANGE', stream, start, end, b'COUNT', count]
            result = await cr(*args)
            return self.transformXRevRangeResponse(result)
        else:
            assert False, 'not implemented'

    def transformXReadResponse(self, response):
        items = []
        for item in response[0][1]:
            position = item[0]
            array = item[1]
            entries = {}

            for i in range(len(array) // 2):
                key = array[2 * i]
                value = array[2 * i + 1]
                entries[key] = value

            items.append((position, entries))
        return {response[0][0]: items}

    def transformXRevRangeResponse(self, response):
        items = []
        for item in response:
            position = item[0]
            array = item[1]
            entries = {}

            for i in range(len(array) // 2):
                key = array[2 * i]
                value = array[2 * i + 1]
                entries[key] = value

            items.append((position, entries))
        return items

'''rcc redis client

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

from rcc.client import RedisClient


class RedisClientRcc(object):
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

        self.redis = RedisClient(self.url, self.password)

        self.host = host

    def __del__(self):
        self.close()

    def close(self):
        # FIXME we should call aclose for justredis
        pass

    async def connect(self):
        pass

    async def ping(self):
        return await self.redis.send('PING')

    async def xadd(self, stream, field, data, maxLen):
        return await self.redis.send(
            'XADD', stream, 'MAXLEN', '~', maxLen, b'*', field, data
        )

    async def exists(self, key):
        return await self.redis.send('EXISTS', key)

    async def xread(self, streams):
        args = ['XREAD', 'BLOCK', b'0', b'STREAMS']
        for item in streams.items():
            args.append(item[0])
            args.append(item[1])

        result = await self.redis.send(*args)
        return result

    async def delete(self, key):
        return await self.redis.send('DEL', key)

    async def xrevrange(self, stream, start, end, count):
        return await self.redis.send('XREVRANGE', stream, start, end, b'COUNT', count)

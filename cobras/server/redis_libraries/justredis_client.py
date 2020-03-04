'''justredis redis client

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from urllib.parse import urlparse

from cobras.server.justredis import Multiplexer


class RedisClientJustRedis(object):
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

        self.redis = Multiplexer({'endpoints': (host, port)})
        self.db = self.redis.database()

        self.host = host

    def __del__(self):
        self.close()

    async def closeMultiplexer(self):
        await self.redis.aclose()

    def close(self):
        # asyncio.get_event_loop().run_until_complete(self.closeMultiplexer())
        pass

    async def connect(self):
        pass

    async def ping(self):
        cr = self.db.commandreply
        return await cr(b'PING')

    async def xadd(self, stream, field, data, maxLen):
        cr = self.db.commandreply
        return await cr('XADD', stream, 'MAXLEN', '~', maxLen, b'*', field, data)

    async def exists(self, key):
        cr = self.db.commandreply
        return await cr(b'EXISTS', key)

    async def xread(self, streams):
        args = ['XREAD', 'BLOCK', b'0', b'STREAMS']
        for item in streams.items():
            args.append(item[0])
            args.append(item[1])

        cr = self.db.commandreply
        result = await cr(*args)
        return self.transformXReadResponse(result)

    async def delete(self, key):
        cr = self.db.commandreply
        return await cr(b'DEL', key)

    async def xrevrange(self, stream, start, end, count):
        cr = self.db.commandreply
        args = ['XREVRANGE', stream, start, end, b'COUNT', count]
        result = await cr(*args)
        return self.transformXRevRangeResponse(result)

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

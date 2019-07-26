'''Custom 'publish only' redis client which uses redis PIPELINING

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio


class RedisPublisher(object):
    '''
    See https://redis.io/topics/mass-insert
    '''
    def __init__(self, host, port, password, verbose=False):
        self.host = host
        self.port = port
        self.password = password
        self.verbose = verbose
        self.reset()
        self.lock = asyncio.Lock()

    def reset(self):
        self.publishCount = 0

    async def connect(self):
        async with self.lock:
            print(f'Opening connection to redis at {self.host}:{self.port}')
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port)

        if self.password:
            self.writer.write(b'*2\r\n')
            self.writeString(b'AUTH')

            password = self.password
            if not isinstance(password, bytes):
                password = password.encode('utf8')

            self.writeString(password)
            await self.execute()

    async def execute(self):
        async with self.lock:
            await self.writer.drain()

            results = []

            # read until we get something
            for i in range(self.publishCount):
                line = await self.reader.readline()
                results.append(line)

                # FIXME: proper error handling !!!
                if self.verbose:
                    print(f'Received: {line.decode()!r}')

                if 'NOAUTH Authentication required' in line.decode():
                    raise ValueError('Authentication failed')

            self.reset()

            return results

    def close(self):
        print('Close the connection')
        self.reset()
        self.writer.close()

    async def wait_closed(self):
        await self.writer.wait_closed()

    def publish(self, channel, msg):
        self.publishCount += 1

        if not isinstance(channel, bytes):
            channel = channel.encode('utf8')

        if not isinstance(msg, bytes):
            msg = msg.encode('utf8')

        self.writer.write(b'*3\r\n')
        self.writeString(b'PUBLISH')
        self.writeString(channel)
        self.writeString(msg)

    def writeString(self, data: bytes):
        # import pdb; pdb.set_trace()
        # data = data.encode('utf-8')

        self.writer.write(b'$%d\r\n' % len(data))
        self.writer.write(data)
        self.writer.write(b'\r\n')


async def create_redis_publisher(host, port, password, verbose=False):
    client = RedisPublisher(host, port, password, verbose)
    await client.connect()
    return client

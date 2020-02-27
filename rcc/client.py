'''Redis client

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.

TODO:
    RESP3 support (start by sending hello3) / then use hash types
'''

import asyncio
import logging

import hiredis

from rcc.hash_slot import getHashSlot
from rcc.pool import ConnectionPool

from rcc.commands.cluster import ClusterCommandsMixin
from rcc.commands.pubsub import PubSubCommandsMixin
from rcc.response import ResponseConverterMixin


class RedisClient(ClusterCommandsMixin, PubSubCommandsMixin, ResponseConverterMixin):
    def __init__(self, url: str, password):
        self.url = url
        self.password = password

        self.urls = {}
        self.pool = ConnectionPool(password)
        self.connection = self.pool.get(self.url)
        self.cluster = False
        self.lock = asyncio.Lock()

    def __del__(self):
        '''
        It is a smell that we have to do this manually,
        but without it we get a big resource leak
        '''
        self.close()

    def close(self):
        self.pool.flush()

    @property
    def host(self):
        return self.connection.host

    @property
    def port(self):
        return self.connection.port

    async def connect(self):
        await self.connection.connect()

        info = await self.send('INFO')
        self.cluster = info.get('cluster_enabled') == '1'

        if self.cluster:
            await self.connect_cluster_nodes()

    async def connect_cluster_nodes(self):
        nodes = await self.cluster_nodes()
        for node in nodes:
            if node.role == 'master':
                url = f'redis://{node.ip}:{node.port}'
                await self.setConnection(node.slots, url)

    async def readResponse(self, connection):
        response = await connection.readResponse()
        return response

    async def getConnection(self, key):
        hashSlot = None
        if key is not None:
            hashSlot = getHashSlot(key)

        url = self.urls.get(hashSlot, self.url)
        connection = self.pool.get(url)

        msg = f'key {key} -> slot {hashSlot}'
        msg += f' -> connection {connection.host}:{connection.port}'
        logging.debug(msg)

        return connection

    async def setConnection(self, slots, url: str):
        connection = self.pool.get(url)
        await connection.connect()

        for slot in slots:
            self.urls[slot] = url

    def findKey(self, cmd, *args):
        '''Find where the key lives in a command, so that it can be hashed
        with crc16.
        '''

        if cmd in ('XREAD', 'XREADGROUP'):
            idx = -1
            for i, arg in enumerate(args):
                if arg in (b'STREAMS', 'STREAMS'):
                    idx = i

            if idx == -1:
                raise ValueError(f"{cmd} arguments '{args}' do not contain STREAMS")
            else:
                idx = idx + 1
            key = args[idx]
        elif cmd in ('XGROUP', 'XINFO'):
            key = args[1]
        else:
            key = None if len(args) == 0 else args[0]

        return key

    async def send(self, cmd, *args):
        '''Send a command to the redis server.
        Handle cluster mode redirects with the MOVE response
        '''
        # We need to extract the key to hash it in cluster mode
        key = self.findKey(cmd, *args)

        # key is at different spot than first args for some commands such as STREAMS
        attempts = 10

        async with self.lock:
            while attempts > 0:
                # we should optimize this for the common case
                connection = await self.getConnection(key)

                await connection.send(cmd, key, *args)
                response = await self.readResponse(connection)

                responseType = type(response)
                if responseType != hiredis.ReplyError:
                    return self.convert(response, cmd)

                attempts -= 1

                responseStr = str(response)
                if responseStr.startswith('MOVED'):
                    tokens = responseStr.split()
                    slotStr = tokens[1]
                    slot = int(slotStr)
                    url = tokens[2]
                    url = 'redis://' + url

                    await self.setConnection([slot], url)
                else:
                    raise response

        raise ValueError(f'Error sending command, too many redirects: {cmd} {args}')

    def __repr__(self):
        return f'<RedisClient at {self.host}:{self.port}>'

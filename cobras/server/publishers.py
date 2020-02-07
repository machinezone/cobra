'''Publishers management

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio

from cobras.server.publisher import Publisher
from cobras.server.redis_connections import RedisConnections


class Publishers:
    def __init__(
        self,
        redisConnections: RedisConnections,
        batchPublishSize: int,
        channelMaxLength: int,
    ) -> None:
        self.redisConnections = redisConnections
        self.publishers: dict = {}
        self.batchPublishSize: int = batchPublishSize
        self.channelMaxLength: int = channelMaxLength
        self.lock = asyncio.Lock()

    def close(self):
        for publisher in self.publishers.values():
            publisher.close()

    def getAppChannelAndKey(self, appkey, channel):
        '''
        Constraints:
        * (A) For a given app, subscriptions and publish should go to the
          same redis node.
        * (B) Each app should get its own redis connection,
          so that one 'busy' app does not block another one.

        Those constraints are reflected in the way we compute the hashing key
        '''
        # Constraint A
        appChannel = '{}::{}'.format(appkey, channel)

        # Constraint B
        key = '{}::{}'.format(appkey, self.redisConnections.hashChannel(appChannel))

        return appChannel, key

    async def get(self, appkey, channel):
        appChannel, key = self.getAppChannelAndKey(appkey, channel)

        async with self.lock:
            publisher = self.publishers.get(key)
            if publisher is not None:
                return publisher

            db = await self.redisConnections.create(appChannel)
            publisher = Publisher(db, self.batchPublishSize, self.channelMaxLength)
            self.publishers[key] = publisher
            return publisher

    async def erasePublisher(self, appkey, channel):
        appChannel, key = self.getAppChannelAndKey(appkey, channel)

        async with self.lock:
            publisher = self.publishers.get(key)
            if publisher is not None:
                publisher.close()
                del self.publishers[key]

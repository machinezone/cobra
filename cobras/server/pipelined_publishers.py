'''Publishers management

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio

from cobras.server.pipelined_publisher import PipelinedPublisher
from cobras.server.redis_connections import RedisConnections


class PipelinedPublishers:
    def __init__(
        self,
        redisConnections: RedisConnections,
        batchPublishSize: int,
        channelMaxLength: int,
    ) -> None:
        self.redisConnections = redisConnections
        self.pipelinedPublishers: dict = {}
        self.batchPublishSize: int = batchPublishSize
        self.channelMaxLength: int = channelMaxLength
        self.lock = asyncio.Lock()

    def close(self):
        for pipelinedPublisher in self.pipelinedPublishers.values():
            pipelinedPublisher.close()

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
            pipelinedPublisher = self.pipelinedPublishers.get(key)
            if pipelinedPublisher is not None:
                return pipelinedPublisher

            db = await self.redisConnections.create(appChannel)
            pipelinedPublisher = PipelinedPublisher(
                db, self.batchPublishSize, self.channelMaxLength
            )
            self.pipelinedPublishers[key] = pipelinedPublisher
            return pipelinedPublisher

    async def erasePublisher(self, appkey, channel):
        appChannel, key = self.getAppChannelAndKey(appkey, channel)

        async with self.lock:
            pipelinedPublisher = self.pipelinedPublishers.get(key)
            if pipelinedPublisher is not None:
                pipelinedPublisher.close()
                del self.pipelinedPublishers[key]

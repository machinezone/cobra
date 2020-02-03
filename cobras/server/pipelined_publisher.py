'''Publish jobs gets enqueued into a multi-publisher, which publish them
to redis in a batch fashion, using a pipeline.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

https://redis.io/topics/pipelining
Weird leaks https://bugs.python.org/issue31620
'''

import asyncio
import logging
from typing import Optional


class PipelinedPublisher:
    def __init__(self, redis, batchSize=None, channelMaxLength=None):
        self.redis = redis
        self.queue = asyncio.Queue()
        self.batchSize = batchSize or 100
        self.xaddMaxLength = channelMaxLength or 1000
        self.lock = asyncio.Lock()

    def close(self):
        try:
            self.redis.close()
        except Exception as e:
            logging.error('Error while closing redis %s', e)
            raise

    async def publishAll(self):
        pipe = self.redis.pipeline()
        async with self.lock:
            while True:
                try:
                    job = self.queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                else:
                    self.publish(pipe, job)
                    self.queue.task_done()

        await pipe.execute()

    def enqueue(self, job):
        self.queue.put_nowait(job)

    def publish(self, pipe, job, maxLen: Optional[int] = None):
        if maxLen is None:
            maxLen = self.xaddMaxLength

        appkey, channel, data = job
        appChannel = '{}::{}'.format(appkey, channel)

        redis = pipe if pipe is not None else self.redis
        redis.xadd(
            appChannel, {'json': data}, max_len=self.xaddMaxLength, exact_len=False
        )

    async def publishNow(self, job, maxLen: Optional[int] = None):
        async with self.lock:
            self.publish(None, job, maxLen)

    async def push(self, job, batchPublish=False):
        if not batchPublish:
            await self.publishNow(job)
            return

        self.enqueue(job)

        if self.queue.qsize() >= self.batchSize:
            await self.publishAll()

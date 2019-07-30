'''Publish jobs gets enqueued into a multi-publisher, which publish them
to redis in a batch fashion, using a pipeline.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

https://redis.io/topics/pipelining
Weird leaks https://bugs.python.org/issue31620
'''

import asyncio


class PipelinedPublisher():
    def __init__(self, redis, batchSize=None):
        self.redis = redis
        self.queue = asyncio.Queue()
        self.batchSize = batchSize or 100
        self.lock = asyncio.Lock()

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

    def publish(self, pipe, job):
        appkey, channel, data = job
        appChannel = '{}::{}'.format(appkey, channel)
        pipe.xadd(appChannel, {'json': data},
                  max_len=100, exact_len=False)

    async def publishNow(self, job):
        async with self.lock:
            pipe = self.redis.pipeline()
            self.publish(pipe, job)
            await pipe.execute()

    async def push(self, job, batchPublish=False):
        if not batchPublish:
            await self.publishNow(job)
            return

        self.enqueue(job)

        if self.queue.qsize() >= self.batchSize:
            await self.publishAll()

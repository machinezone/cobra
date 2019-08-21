'''Capture statistics (publisher, subscribers, sent+received bytes, message
count, etc...). Used by `cobra monitor`

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import collections
import datetime
import json
import os
import platform
import time
import logging

from cobras.common.memory_usage import getContainerMemoryLimit, getProcessUsedMemory

DEFAULT_STATS_CHANNEL = '/stats'


class ServerStats:
    def __init__(self, pipelinedPublishers, appkey):
        self.pipelinedPublishers = pipelinedPublishers

        self.node = platform.uname().node
        self.connectionCount = 0
        self.stop = False

        self.idleConnections = 0

        self.internalAppKey = appkey
        self.statsChannel = DEFAULT_STATS_CHANNEL

        self.publishedCount = collections.defaultdict(int)
        self.publishedBytes = collections.defaultdict(int)
        self.subscribedCount = collections.defaultdict(int)
        self.subscribedBytes = collections.defaultdict(int)
        self.subscriptions = collections.defaultdict(int)

        self.readsCount = collections.defaultdict(int)
        self.readsBytes = collections.defaultdict(int)
        self.writesCount = collections.defaultdict(int)
        self.writesBytes = collections.defaultdict(int)

        self.resetCounterByPeriod()
        self.start = time.time()

        print('node ' + self.node)

    def incrConnections(self, role):
        self.connectionCount += 1

    def decrConnections(self, role):
        self.connectionCount -= 1

    def incrIdleConnections(self):
        self.idleConnections += 1

    def incrSubscriptions(self, role):
        self.subscriptions[role] += 1

    def decrSubscriptionsBy(self, role, subscriptionsCount):
        self.subscriptions[role] -= subscriptionsCount

    def resetCounterByPeriod(self):
        self.publishedCountByPeriod = collections.defaultdict(int)
        self.publishedBytesByPeriod = collections.defaultdict(int)
        self.subscribedCountByPeriod = collections.defaultdict(int)
        self.subscribedBytesByPeriod = collections.defaultdict(int)

        self.readsCountByPeriod = collections.defaultdict(int)
        self.readsBytesByPeriod = collections.defaultdict(int)
        self.writesCountByPeriod = collections.defaultdict(int)
        self.writesBytesByPeriod = collections.defaultdict(int)

    def updatePublished(self, role, val):
        self.publishedCount[role] += 1
        self.publishedBytes[role] += val

        self.publishedCountByPeriod[role] += 1
        self.publishedBytesByPeriod[role] += val

    def updateSubscribed(self, role, val):
        self.subscribedCount[role] += 1
        self.subscribedBytes[role] += val

        self.subscribedCountByPeriod[role] += 1
        self.subscribedBytesByPeriod[role] += val

    def updateReads(self, role, val):
        self.readsCount[role] += 1
        self.readsBytes[role] += val

        self.readsCountByPeriod[role] += 1
        self.readsBytesByPeriod[role] += val

    def updateWrites(self, role, val):
        self.writesCount[role] += 1
        self.writesBytes[role] += val

        self.writesCountByPeriod[role] += 1
        self.writesBytesByPeriod[role] += val

    async def run(self):
        while True:
            # Only dict-like objects are permitted in that field
            # to ease the job of aggregating them in the monitor command
            cobraData = {'subscriptions': self.subscriptions}

            cobraData.update(
                {
                    'published_count': self.publishedCount,
                    'published_bytes': self.publishedBytes,
                    'published_count_per_second': self.publishedCountByPeriod,
                    'published_bytes_per_second': self.publishedBytesByPeriod,
                }
            )

            cobraData.update(
                {
                    'subscribed_count': self.subscribedCount,
                    'subscribed_bytes': self.subscribedBytes,
                    'subscribed_count_per_second': self.subscribedCountByPeriod,
                    'subscribed_bytes_per_second': self.subscribedBytesByPeriod,
                }
            )

            cobraData.update(
                {
                    'reads_count': self.readsCount,
                    'reads_bytes': self.readsBytes,
                    'reads_count_per_second': self.readsCountByPeriod,
                    'reads_bytes_per_second': self.readsBytesByPeriod,
                }
            )

            cobraData.update(
                {
                    'writes_count': self.writesCount,
                    'writes_bytes': self.writesBytes,
                    'writes_count_per_second': self.writesCountByPeriod,
                    'writes_bytes_per_second': self.writesBytesByPeriod,
                }
            )

            uptime = time.time() - self.start
            uptimeMinutes = uptime // 60
            uptime = str(datetime.timedelta(seconds=uptime))
            uptime, _, _ = uptime.partition('.')  # skip the milliseconds part

            message = {
                'node': self.node,
                'prod': os.getenv('COBRA_PROD') is not None,
                'data': {
                    'cobra': cobraData,
                    'system': {
                        'connections': self.connectionCount,
                        'mem_bytes': getProcessUsedMemory(),
                        'container_memory_limit_bytes': getContainerMemoryLimit(),  # noqa
                        'uptime': uptime,
                        'uptime_minutes': uptimeMinutes,
                        'tasks': len(asyncio.all_tasks()),
                        'idle_connections': self.idleConnections,
                    },
                },
            }

            data = json.dumps({'body': {'message': message}})

            chan = self.statsChannel
            appkey = self.internalAppKey

            try:
                pipelinedPublisher = await self.pipelinedPublishers.get(appkey, chan)
                await pipelinedPublisher.publishNow((appkey, chan, data))
            except Exception as e:
                logging.error(f"stats: cannot connect to redis {e}")
                pass

            self.resetCounterByPeriod()

            # Sleep 1 second
            await asyncio.sleep(1)

            if self.stop:
                return

    def terminate(self):
        self.stop = True

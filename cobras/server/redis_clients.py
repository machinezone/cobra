'''Manage redis clients, owned by the app

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import sys
import time
import logging

from rcc.client import RedisClient


class RedisClients(object):
    def __init__(self, redisUrls, redisPassword, appsConfig):
        self.redisUrls = redisUrls
        self.redisPassword = redisPassword
        self.clients = {}

        for app in appsConfig.apps:
            self.clients[app] = self.makeRedisClient()

    def makeRedisClient(self):
        return RedisClient(self.redisUrls, self.redisPassword)

    def getRedisClient(self, appkey):
        return self.clients.get(appkey)

    def closeRedis(self):
        # FIXME / close all
        print('closeRedis not implemented ... FIXME')

    async def waitForAllConnectionsToBeReady(self, timeout: int):
        start = time.time()

        urls = self.redisUrls.split(';')

        for url in urls:
            sys.stderr.write(f'Checking {url} ')

            while True:
                sys.stderr.write('.')
                sys.stderr.flush()

                try:
                    redis = RedisClient(url, self.redisPassword)
                    await redis.connect()
                    await redis.ping()
                    redis.close()
                    break
                except Exception as e:
                    if time.time() - start > timeout:
                        sys.stderr.write('\n')
                        raise

                    logging.warning(e)

                    waitTime = 0.1
                    await asyncio.sleep(waitTime)
                    timeout -= waitTime

            sys.stderr.write('\n')

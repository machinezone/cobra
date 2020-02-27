'''Manage redis clients, owned by the app

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import sys
import time
import logging

from rcc.client import RedisClient
from rcc.cluster.init_cluster import waitForAllConnectionsToBeReady


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
        urls = self.redisUrls.split(';')
        await waitForAllConnectionsToBeReady(urls, self.redisPassword, timeout)

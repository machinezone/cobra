'''Manage redis clients, owned by the app

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

from cobras.server.redis_client import RedisClient


class RedisClients(object):
    def __init__(self, redisUrls, redisPassword, redisCluster, library, appsConfig):
        self.redisUrls = redisUrls
        self.redisPassword = redisPassword
        self.redisCluster = redisCluster
        self.library = library
        self.clients = {}

        for app in appsConfig.apps:
            self.clients[app] = self.makeRedisClient()

    def makeRedisClient(self):
        return RedisClient(
            self.redisUrls, self.redisPassword, self.redisCluster, self.library
        )

    def getRedisClient(self, appkey):
        return self.clients.get(appkey)

    def closeRedis(self):
        # FIXME / close all
        print('closeRedis not implemented ... FIXME')

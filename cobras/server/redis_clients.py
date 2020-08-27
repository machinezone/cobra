'''Manage redis clients, owned by the app

Copyright (c) 2018-2020 Machine Zone, Inc. All rights reserved.
'''

from cobras.server.rcc_client import RedisClientRcc


class RedisClients(object):
    def __init__(self, redisUrls, redisPassword, redisCluster, appsConfig):
        self.redisUrls = redisUrls
        self.redisPassword = redisPassword
        self.redisCluster = redisCluster
        self.clients = {}

        for app in appsConfig.apps:
            self.clients[app] = self.makeRedisClient()

    def makeRedisClient(self):
        return RedisClientRcc(self.redisUrls, self.redisPassword, self.redisCluster)

    def getRedisClient(self, appkey):
        return self.clients.get(appkey)

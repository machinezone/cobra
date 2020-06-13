'''Manage redis clients, owned by the app

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

# from cobras.server.redis_client import RedisClient
from cobras.server.redis_libraries.aredis_client import RedisClientAredis
from cobras.server.redis_libraries.rcc_client import RedisClientRcc
from cobras.server.redis_libraries.justredis_client import RedisClientJustRedis
from cobras.server.redis_libraries.aioredis_client import RedisClientAioRedis

DEFAULT_REDIS_LIBRARY = 'rcc'


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
        if self.library == 'aredis':
            klass = RedisClientAredis
        elif self.library == 'rcc':
            klass = RedisClientRcc
        elif self.library == 'justredis':
            klass = RedisClientJustRedis
        elif self.library == 'aioredis':
            klass = RedisClientAioRedis

        return klass(
            self.redisUrls, self.redisPassword, self.redisCluster, self.library
        )

    def getRedisClient(self, appkey):
        return self.clients.get(appkey)

    def closeRedis(self):
        # FIXME / close all
        print('closeRedis not implemented ... FIXME')

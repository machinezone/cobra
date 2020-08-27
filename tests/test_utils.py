'''Copyright (c) 2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import os
import random
import tempfile
import uuid

import coloredlogs
from cobras.common.apps_config import AppsConfig, getDefaultMessageMaxSize
from cobras.server.app import AppRunner

coloredlogs.install(level='INFO')


def getFreePort():
    return random.randint(9000, 16000)


def makeRunner(
    debugMemory=False, enableStats=False, redisUrls=None, probeRedisOnStartup=True
):
    host = 'localhost'
    port = getFreePort()
    redisPassword = None
    plugins = 'republish'
    maxSubscriptions = -1
    idleTimeout = 10  # after 10 seconds it's a lost cause / FIXME(unused)
    debugMemoryNoTracemalloc = False
    debugMemoryPrintAllTasks = False

    redisCluster = False

    if redisUrls is None:
        if redisCluster:
            redisUrls = 'redis://localhost:11000'
        else:
            redisUrls = 'redis://localhost'

    appsConfigPath = tempfile.mktemp()
    appsConfig = AppsConfig(appsConfigPath)
    appsConfig.generateDefaultConfig()
    os.environ['COBRA_APPS_CONFIG'] = appsConfigPath

    runner = AppRunner(
        host,
        port,
        redisUrls,
        redisPassword,
        redisCluster,
        appsConfigPath,
        debugMemory,
        debugMemoryNoTracemalloc,
        debugMemoryPrintAllTasks,
        plugins,
        enableStats,
        maxSubscriptions,
        idleTimeout,
        probeRedisOnStartup,
        redisStartupProbingTimeout=5,
        messageMaxSize=getDefaultMessageMaxSize(),
    )
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, appsConfigPath


def makeUniqueString():
    return uuid.uuid4().hex

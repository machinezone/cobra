'''Copyright (c) 2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import os
import random
import tempfile
import uuid

import coloredlogs
from cobras.common.apps_config import AppsConfig
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

    if redisUrls is None:
        # redisUrls = 'redis://localhost'
        redisUrls = 'redis://localhost:10000'  # to run against a redis cluster

    appsConfigPath = tempfile.mktemp()
    appsConfig = AppsConfig(appsConfigPath)
    appsConfig.generateDefaultConfig()
    os.environ['COBRA_APPS_CONFIG'] = appsConfigPath

    runner = AppRunner(
        host,
        port,
        redisUrls,
        redisPassword,
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
    )
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, appsConfigPath


def makeUniqueString():
    return uuid.uuid4().hex

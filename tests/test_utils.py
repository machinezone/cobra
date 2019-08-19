'''Copyright (c) 2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import tempfile
import os
import random

from cobras.common.apps_config import AppsConfig
from cobras.server.app import AppRunner

import coloredlogs
coloredlogs.install(level='INFO')


def getFreePort():
    return random.randint(9000, 16000)


def makeRunner(debugMemory=False):
    host = 'localhost'
    port = getFreePort()
    redisUrls = 'redis://localhost'
    redisPassword = None
    plugins = 'republish'
    enableStats = True
    maxSubscriptions = -1
    idleTimeout = 10  # after 10 seconds it's a lost cause

    appsConfigPath = tempfile.mktemp()
    appsConfig = AppsConfig(appsConfigPath)
    appsConfig.generateDefaultConfig()
    os.environ['COBRA_APPS_CONFIG'] = appsConfigPath

    runner = AppRunner(host, port, redisUrls, redisPassword, appsConfigPath,
                       debugMemory, plugins, enableStats,
                       maxSubscriptions, idleTimeout)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, appsConfigPath


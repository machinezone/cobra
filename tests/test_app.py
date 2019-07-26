'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import gc

from cobra.client.credentials import (getDefaultRoleForApp,
                                      getDefaultSecretForApp)
from cobra.client.health_check import (getDefaultHealthCheckHttpUrl,
                                       getDefaultHealthCheckUrl, healthCheck)
from cobra.common.apps_config import getDefaultAppsConfigPath
from cobra.common.memory_debugger import MemoryDebugger
from cobra.server.app import AppRunner


def createAppRunner(debugMemory=False):
    host = 'localhost'
    port = '5678'
    redisUrls = 'redis://localhost'
    redisPassword = None
    verbose = True
    plugins = 'republish'
    enableStats = True
    maxSubscriptions = -1
    idleTimeout = 10  # after 10 seconds it's a lost cause

    runner = AppRunner(host, port, redisUrls, redisPassword,
                       getDefaultAppsConfigPath(), verbose, debugMemory,
                       plugins, enableStats, maxSubscriptions, idleTimeout)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, port


def test_server():
    '''Starts a server, then run a health check'''
    runner, port = createAppRunner()

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    # Run 2 health-checks in a row
    healthCheck(url, role, secret, channel)
    healthCheck(url, role, secret, channel)

    runner.terminate()


def test_server_again():
    '''This make sure that we cleanup our server properly,
    and to run the debugMemory code
    '''
    runner, port = createAppRunner(debugMemory=True)

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    healthCheck(url, role, secret, channel)

    runner.terminate()


def runTest():
    runner, port = createAppRunner(debugMemory=True)

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    for i in range(5):
        healthCheck(url, role, secret, channel)

    runner.terminate()


def test_server_mem():
    '''This make sure that we cleanup our server properly,
    and to run the debugMemory code
    '''
    memoryDebugger = MemoryDebugger(0.1, 2, 'traceback')
    memoryDebugger.collect_stats()
    runTest()

    gc.collect()
    memoryDebugger.collect_stats()

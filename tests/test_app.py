'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import gc
import os
import tempfile

import pytest

from cobras.client.credentials import (getDefaultRoleForApp,
                                       getDefaultSecretForApp)
from cobras.client.health_check import (getDefaultHealthCheckHttpUrl,
                                        getDefaultHealthCheckUrl, healthCheck)
from cobras.common.apps_config import AppsConfig
from cobras.common.memory_debugger import MemoryDebugger
from cobras.server.app import AppRunner


def makeRunner(debugMemory=False):
    host = 'localhost'
    port = '5678'
    redisUrls = 'redis://localhost'
    redisPassword = None
    verbose = True
    plugins = 'republish'
    enableStats = True
    maxSubscriptions = -1
    idleTimeout = 10  # after 10 seconds it's a lost cause

    appsConfigPath = tempfile.mktemp()
    appsConfig = AppsConfig(appsConfigPath)
    appsConfig.generateDefaultConfig()
    os.environ['COBRA_APPS_CONFIG'] = appsConfigPath

    runner = AppRunner(host, port, redisUrls, redisPassword,
                       appsConfigPath, verbose, debugMemory,
                       plugins, enableStats, maxSubscriptions, idleTimeout)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, appsConfigPath


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


@pytest.fixture()
def debugMemoryRunner():
    runner, appsConfigPath = makeRunner(debugMemory=True)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


def test_server(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    # Run 2 health-checks in a row
    healthCheck(url, role, secret, channel)
    healthCheck(url, role, secret, channel)


def test_server_again(debugMemoryRunner):
    '''This make sure that we cleanup our server properly,
    and to run the debugMemory code
    '''
    port = debugMemoryRunner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    healthCheck(url, role, secret, channel)


def runTest(port):
    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = 'foo'

    for i in range(5):
        healthCheck(url, role, secret, channel)


def test_server_mem(debugMemoryRunner):
    '''This make sure that we cleanup our server properly,
    and to run the debugMemory code
    '''
    memoryDebugger = MemoryDebugger(0.1, 2, 'traceback')
    memoryDebugger.collect_stats()
    runTest(debugMemoryRunner.port)

    gc.collect()
    memoryDebugger.collect_stats()

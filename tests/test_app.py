'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import gc
import os
import asyncio

import pytest
from cobras.client.credentials import getDefaultRoleForApp, getDefaultSecretForApp
from cobras.client.health_check import getDefaultHealthCheckUrl, healthCheck
from cobras.common.memory_debugger import MemoryDebugger

from .test_utils import makeRunner, makeUniqueString


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
    channel = makeUniqueString()

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
    channel = makeUniqueString()

    healthCheck(url, role, secret, channel)


def runTest(port):
    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = makeUniqueString()

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


async def startAndProbRedisExpectSuccess(runner):
    # FIXME / move this test to its own file
    await runner.redisClients.waitForAllConnectionsToBeReady(1)


def test_redis_startup_probing_success(runner):
    asyncio.get_event_loop().run_until_complete(startAndProbRedisExpectSuccess(runner))

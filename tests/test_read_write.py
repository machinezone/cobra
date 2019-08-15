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
from cobras.client.credentials import createCredentials
from cobras.client.connection import Connection
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

    runner = AppRunner(host, port, redisUrls, redisPassword, appsConfigPath,
                       verbose, debugMemory, plugins, enableStats,
                       maxSubscriptions, idleTimeout)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    return runner, appsConfigPath


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


async def clientCoroutine(connection):
    await connection.connect()

    channel = 'foo'
    data = {"foo": "bar"}
    await connection.write(channel, data)
    receivedData = await connection.read(channel)

    assert receivedData == data

    await connection.close()


def test_read_write(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection))

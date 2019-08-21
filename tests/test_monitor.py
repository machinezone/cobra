'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import gc
import os
import tempfile
import uuid

import pytest

from cobras.client.credentials import getDefaultRoleForApp, getDefaultSecretForApp
from cobras.client.health_check import (
    getDefaultHealthCheckHttpUrl,
    getDefaultHealthCheckUrl,
    healthCheck,
)
from cobras.common.memory_debugger import MemoryDebugger
from cobras.client.credentials import createCredentials
from cobras.client.connection import Connection
from cobras.client.monitor import runMonitor, getDefaultMonitorUrl

from .test_utils import makeRunner


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(enableStats=True)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


def makeUniqueString():
    return uuid.uuid4().hex


async def clientCoroutine(connection):
    # Wait a bit
    await asyncio.sleep(0.1)

    await connection.connect()

    for i in range(10):
        channel = makeUniqueString()
        data = {"foo": makeUniqueString()}
        await connection.write(channel, data)

    await connection.close()


def monitor(connection):
    return runMonitor(
        connection.url,
        connection.creds,
        raw=True,
        roleFilter=None,
        showNodes=True,
        showRoles=True,
        subscribers=True,
        system=False,
        once=True,
    )


def test_monitor(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultMonitorUrl(None, port)
    role = getDefaultRoleForApp('stats')
    secret = getDefaultSecretForApp('stats')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection))
    messageHandler = monitor(connection)
    print(messageHandler)

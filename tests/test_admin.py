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
from cobras.common.memory_debugger import MemoryDebugger
from cobras.client.credentials import createCredentials
from cobras.client.connection import Connection

from .test_utils import makeRunner


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


async def clientCoroutine(connection, connectionToBeClosed):
    await connection.connect()
    await connectionToBeClosed.connect()

    openedConnections = await connection.adminGetConnections()
    assert len(openedConnections) == 2

    await connection.adminCloseConnection(connectionToBeClosed.connectionId)

    openedConnections = await connection.adminGetConnections()
    assert len(openedConnections) == 1

    await connection.close()


def test_admin_disconnect_one(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)
    connectionToBeClosed = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection,
                                                                connectionToBeClosed))

'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import os
import uuid

import pytest

from cobras.client.credentials import getDefaultRoleForApp, getDefaultSecretForApp
from cobras.client.credentials import createCredentials
from cobras.client.connection import Connection
from cobras.client.connection import ActionException
from cobras.client.health_check import getDefaultHealthCheckUrl

from .test_utils import makeRunner


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


@pytest.fixture()
def redisDownRunner():
    redisUrls = 'redis://localhost:9999'
    runner, appsConfigPath = makeRunner(
        debugMemory=False, enableStats=False, redisUrls=redisUrls
    )
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


def makeUniqueString():
    return uuid.uuid4().hex


async def clientCoroutine(connection):
    await connection.connect()

    channel = makeUniqueString()
    data = {"foo": makeUniqueString()}
    await connection.write(channel, data)
    receivedData = await connection.read(channel)

    assert receivedData == data

    # Delete that entry previous one
    await connection.delete(channel)
    receivedData = await connection.read(channel)
    assert receivedData is None

    # Read a missing entry, make sure its empty
    receivedData = await connection.read(makeUniqueString())
    assert receivedData is None

    await connection.close()


def test_read_write_delete(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection))


async def redisDownClientCoroutine(connection):
    await connection.connect()

    # Test write which should fail
    channel = makeUniqueString()
    with pytest.raises(ActionException):
        data = {"foo": makeUniqueString()}
        await connection.write(channel, data)

    # Test read which should fail
    with pytest.raises(ActionException):
        await connection.read(channel)

    # Test delete which should fail
    with pytest.raises(ActionException):
        await connection.delete(makeUniqueString())


def test_read_write_delete_redis_down(redisDownRunner):
    '''Starts a server, then run a health check'''
    port = redisDownRunner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(redisDownClientCoroutine(connection))

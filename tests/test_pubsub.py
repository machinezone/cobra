'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

# TODO: test subscribe better

import asyncio
import os

import pytest
from cobras.client.connection import ActionException, Connection
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.client.health_check import getDefaultHealthCheckUrl

from .test_utils import makeRunner, makeUniqueString


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


async def clientCoroutine(connection):
    await connection.connect()

    channel = makeUniqueString()
    data = {"foo": makeUniqueString()}
    await connection.publish(channel, data)

    # Missing message
    pdu = {"action": "rtm/publish", "body": {}}
    with pytest.raises(ActionException):
        await connection.send(pdu)

    # Missing channel
    pdu = {"action": "rtm/publish", "body": {'message': 'hello world'}}
    with pytest.raises(ActionException):
        await connection.send(pdu)

    await connection.close()


def test_publish(runner):
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection))


async def redisDownClientCoroutine(connection):
    await connection.connect()

    channel = makeUniqueString()
    data = {"foo": makeUniqueString()}

    # publish should fail if redis is down
    with pytest.raises(ActionException):
        await connection.publish(channel, data)

    await connection.close()


def test_publish_redis_down(redisDownRunner):
    port = redisDownRunner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(redisDownClientCoroutine(connection))


async def subscribeClientCoroutine(connection):
    await connection.connect()

    channel = makeUniqueString()
    data = {"foo": makeUniqueString()}
    await connection.publish(channel, data)

    # Empty body
    pdu = {"action": "rtm/subscribe", "body": {}}
    with pytest.raises(ActionException):
        await connection.send(pdu)

    # Bad stream sql
    pdu = {
        "action": "rtm/subscribe",
        "body": {'channel': 'foo', 'filter': 'bad_filter'},
    }
    with pytest.raises(ActionException):
        await connection.send(pdu)

    # Bad position
    pdu = {
        "action": "rtm/subscribe",
        "body": {'channel': 'foo', 'position': 'bad_position'},
    }
    with pytest.raises(ActionException):
        await connection.send(pdu)

    await connection.close()


def test_subscribe(runner):
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(subscribeClientCoroutine(connection))


async def unsubscribeClientCoroutine(connection):
    await connection.connect()

    channel = makeUniqueString()
    data = {"foo": makeUniqueString()}
    await connection.publish(channel, data)

    # Empty body
    pdu = {"action": "rtm/unsubscribe", "body": {}}
    with pytest.raises(ActionException):
        await connection.send(pdu)

    # Invalid subscription_id
    pdu = {"action": "rtm/unsubscribe", "body": {'subscription_id': 'foo'}}
    with pytest.raises(ActionException):
        await connection.send(pdu)

    await connection.close()


def test_unsubscribe(runner):
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)

    asyncio.get_event_loop().run_until_complete(unsubscribeClientCoroutine(connection))

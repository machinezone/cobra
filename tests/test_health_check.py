'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import os

import pytest
from cobras.client.connection import ActionException
from cobras.client.credentials import getDefaultRoleForApp, getDefaultSecretForApp
from cobras.client.health_check import getDefaultHealthCheckUrl, healthCheck

from .test_utils import makeRunner, makeUniqueString


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


def test_health_check(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = makeUniqueString()

    # Run 2 health-checks in a row
    healthCheck(url, role, secret, channel)


@pytest.fixture()
def redisDownRunner():
    redisUrls = 'redis://localhost:9999'
    runner, appsConfigPath = makeRunner(
        debugMemory=False, enableStats=False, redisUrls=redisUrls
    )
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


def test_health_check_with_no_redis(redisDownRunner):
    '''Starts a server, then run a health check'''
    port = redisDownRunner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')
    channel = makeUniqueString()

    with pytest.raises(ActionException):
        healthCheck(url, role, secret, channel)

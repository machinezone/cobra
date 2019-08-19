'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import gc
import os
import tempfile
import uuid
import logging
from typing import Dict

import pytest

from cobras.client.credentials import (getDefaultRoleForApp,
                                       getDefaultSecretForApp)
from cobras.client.health_check import (getDefaultHealthCheckHttpUrl,
                                        getDefaultHealthCheckUrl, healthCheck)
from cobras.common.memory_debugger import MemoryDebugger
from cobras.client.credentials import createCredentials
from cobras.client.connection import Connection
from cobras.client.client import subscribeClient
from cobras.common.throttle import Throttle

from .test_utils import makeRunner


@pytest.fixture()
def runner():
    runner, appsConfigPath = makeRunner(debugMemory=False)
    yield runner

    runner.terminate()
    os.unlink(appsConfigPath)


class MessageHandlerClass:
    def __init__(self, connection, args):
        self.cnt = 0
        self.cntPerSec = 0
        self.throttle = Throttle(seconds=1)
        self.connection = connection

    async def on_init(self):
        pass

    async def handleMsg(self, message: Dict, position: str) -> bool:
        self.cnt += 1
        self.cntPerSec += 1

        if message['iteration'] == 99:
            return False

        logging.info(f'{message} at position {position}')

        # Ultimately, save last message properly processed. 
        # We'd need a transaction here of some sort, to roll back 
        # all the previous stuff in case of a failure.
        savedPositionId = 'saved_position'
        await self.connection.write(savedPositionId, position)

        if self.throttle.exceedRate():
            return True

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return True


def startSubscriber(url, credentials, channel):
    # fetch last position first
    position = '$'
    stream_sql = None
    waitTime = 0.001

    subscriberTask = asyncio.get_event_loop().create_task(
        subscribeClient(url, credentials, channel, position, stream_sql,
                        MessageHandlerClass, {}, waitTime))

    return subscriberTask


async def disconnectSubscriptionConnection(connection):
    openedConnections = await connection.adminGetConnections()
    assert len(openedConnections) == 2

    # Disconnect the other connection
    for openedConnection in openedConnections:
        if openedConnection != connection.connectionId:
            await connection.adminCloseConnection(openedConnection)


async def clientCoroutine(connection, channel, subscriberTask):
    await connection.connect()

    for i in range(100):
        if i in (25, 50, 75):
            await disconnectSubscriptionConnection(connection)

        # publish one message
        await connection.publish(channel, {"iteration": i})

        await asyncio.sleep(0.001)

    await connection.close()

    # wait 100ms
    await asyncio.sleep(0.1)
    subscriberTask.cancel()
    messageHandler = subscriberTask.result()
    assert messageHandler.cnt == 100


def test_save_position(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)
    connectionToBeClosed = Connection(url, creds)

    channel = 'test_save_position_channel::' + uuid.uuid4().hex
    subscriberTask = startSubscriber(url, creds, channel)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection,
                                                                channel,
                                                                subscriberTask))

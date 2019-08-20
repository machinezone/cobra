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
from cobras.client.connection import Connection, ActionFlow
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
        self.args = args

    async def on_init(self):
        pass

    async def handleMsg(self, message: Dict, position: str) -> ActionFlow:
        self.cnt += 1
        self.cntPerSec += 1

        self.args['total'] += 1
        self.args['ids'].append(message['iteration'])

        if message['iteration'] == 99:
            return ActionFlow.STOP

        logging.info(f'{message} at position {position}')

        if self.throttle.exceedRate():
            return ActionFlow.SAVE_POSITION

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return ActionFlow.SAVE_POSITION


def startSubscriber(url, credentials, channel, resumeFromLastPositionId):
    # fetch last position first
    position = '$'
    stream_sql = None
    waitTime = 0.1

    args = {"total": 0, "ids": []}

    subscriberTask = asyncio.get_event_loop().create_task(
        subscribeClient(url, credentials, channel, position, stream_sql,
                        MessageHandlerClass, args, waitTime,
                        resumeFromLastPosition=True,
                        resumeFromLastPositionId=resumeFromLastPositionId))

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

    # wait 100ms so that the subscriber is ready.
    # FIXME: the subscriber should notify this coro instead
    await asyncio.sleep(0.1)

    for i in range(100):
        if i == 50:
            await disconnectSubscriptionConnection(connection)

        # publish one message
        await connection.publish(channel, {"iteration": i})

        await asyncio.sleep(0.001)

    await connection.close()

    # wait 100ms
    await asyncio.sleep(0.1)
    subscriberTask.cancel()
    messageHandler = subscriberTask.result()

    assert messageHandler.args['total'] == 100


def test_save_position(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)
    connectionToBeClosed = Connection(url, creds)

    uniqueId = uuid.uuid4().hex[:8]
    channel = 'test_save_position_channel::' + uniqueId
    resumeFromLastPositionId = 'last_position_id::' + uniqueId
    subscriberTask = startSubscriber(url, creds, channel, resumeFromLastPositionId)

    asyncio.get_event_loop().run_until_complete(clientCoroutine(connection,
                                                                channel,
                                                                subscriberTask))

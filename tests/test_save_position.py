'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio
import logging
import os
import uuid
from typing import Dict, List

import pytest
from cobras.client.client import subscribeClient
from cobras.client.connection import ActionFlow, Connection
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.client.health_check import getDefaultHealthCheckUrl
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

    async def handleMsg(self, messages: List[Dict], position: str) -> ActionFlow:
        '''We can receive the same position twice,
        if it was processed but wasn't saved yet.
        '''
        self.cnt += 1
        self.cntPerSec += 1

        message = messages[0]

        self.args['ids'].add(message['iteration'])

        if message['iteration'] == 99:
            return ActionFlow.STOP

        logging.info(f'{message} at position {position}')

        if self.throttle.exceedRate():
            return ActionFlow.SAVE_POSITION

        print(f"#messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        return ActionFlow.SAVE_POSITION


async def startSubscriber(url, credentials, channel, resumeFromLastPositionId):
    # fetch last position first
    position = '$'
    stream_sql = None
    waitTime = 0.1

    args = {"ids": set()}

    subscriberTask = asyncio.ensure_future(
        subscribeClient(
            url,
            credentials,
            channel,
            position,
            stream_sql,
            MessageHandlerClass,
            args,
            waitTime,
            resumeFromLastPosition=True,
            resumeFromLastPositionId=resumeFromLastPositionId,
        )
    )

    return subscriberTask


async def disconnectSubscriptionConnection(connection):
    hasTwoConnections = False
    for i in range(100):
        openedConnections = await connection.adminGetConnections()
        if len(openedConnections) == 2:
            hasTwoConnections = True
            break
        await asyncio.sleep(0.001)

    assert hasTwoConnections

    # Disconnect the other connection
    for openedConnection in openedConnections:
        if openedConnection != connection.connectionId:
            await connection.adminCloseConnection(openedConnection)


async def clientCoroutine(
    connection, channel, url, credentials, resumeFromLastPositionId
):
    subscriberTask = await startSubscriber(
        url, credentials, channel, resumeFromLastPositionId
    )
    await connection.connect()

    # wait 100ms so that the subscriber is ready.
    # FIXME: the subscriber should notify this coro instead
    await asyncio.sleep(0.1)

    for i in range(100):
        if i in (2, 25, 60, 80, 98):
            await disconnectSubscriptionConnection(connection)

        # publish one message
        await connection.publish(channel, {"iteration": i})

        await asyncio.sleep(0.001)

    await connection.close()

    # wait 8 seconds max
    for i in range(80):
        await asyncio.sleep(0.1)

        if subscriberTask.done():
            break

    subscriberTask.cancel()
    messageHandler = subscriberTask.result()

    assert len(messageHandler.args['ids']) == 100


def test_save_position(runner):
    '''Starts a server, then run a health check'''
    port = runner.port

    url = getDefaultHealthCheckUrl(None, port)
    role = getDefaultRoleForApp('health')
    secret = getDefaultSecretForApp('health')

    creds = createCredentials(role, secret)
    connection = Connection(url, creds)
    _ = Connection(url, creds)

    uniqueId = uuid.uuid4().hex[:8]
    channel = 'test_save_position_channel::' + uniqueId
    resumeFromLastPositionId = 'last_position_id::' + uniqueId

    asyncio.get_event_loop().run_until_complete(
        clientCoroutine(connection, channel, url, creds, resumeFromLastPositionId)
    )

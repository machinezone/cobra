'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging
from typing import Dict, List

import click
from cobras.common.task_cleanup import addTaskCleanup
from cobras.common.memory_debugger import MemoryDebugger
from cobras.client.client import subscribeClient
from cobras.client.connection import ActionFlow
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.common.apps_config import PUBSUB_APPKEY, getDefaultUrl, makeUrl
from cobras.common.throttle import Throttle


class MessageHandlerClass:
    def __init__(self, connection, args):
        self.cnt = 0
        self.cntPerSec = 0
        self.throttle = Throttle(seconds=1)
        self.args = args
        self.position = None

    async def on_init(self):
        memoryDebugger = MemoryDebugger(noTraceMalloc=True)
        self.memoryDebuggerTask = asyncio.create_task(memoryDebugger.run())
        addTaskCleanup(self.memoryDebuggerTask)

        self.statsTask = asyncio.create_task(self.printStats())
        addTaskCleanup(self.statsTask)

    async def printStats(self):
        while True:
            print(
                f"position {self.position} #messages {self.cnt} msg/s {self.cntPerSec}"
            )
            await asyncio.sleep(1)

    async def handleMsg(self, messages: List[Dict], position: str) -> ActionFlow:
        self.cnt += 1
        self.cntPerSec += 1
        self.position = position

        for message in messages:
            logging.info(f'{message} at position {position}')

        if self.throttle.exceedRate():
            return ActionFlow.CONTINUE

        self.cntPerSec = 0

        if self.args['resume_from_last_position']:
            return ActionFlow.SAVE_POSITION

        return ActionFlow.CONTINUE


@click.command()
@click.option('--endpoint', default=getDefaultUrl())
@click.option('--appkey', default=PUBSUB_APPKEY)
@click.option('--rolename', default=getDefaultRoleForApp('pubsub'))
@click.option('--rolesecret', default=getDefaultSecretForApp('pubsub'))
@click.option('--channel', default='sms_republished_v1_neo')
@click.option('--position')
@click.option('--stream_sql')
@click.option('--resume_from_last_position', is_flag=True)
def subscribe(
    endpoint,
    appkey,
    rolename,
    rolesecret,
    channel,
    position,
    stream_sql,
    resume_from_last_position,
):
    '''Subscribe to a channel
    '''
    url = makeUrl(endpoint, appkey)
    credentials = createCredentials(rolename, rolesecret)

    resumeFromLastPositionId = ''
    if resume_from_last_position:
        resumeFromLastPositionId = f'{channel}::{stream_sql}'

    asyncio.get_event_loop().run_until_complete(
        subscribeClient(
            url,
            credentials,
            channel,
            position,
            stream_sql,
            MessageHandlerClass,
            {'resume_from_last_position': resume_from_last_position},
            resumeFromLastPosition=resume_from_last_position,
            resumeFromLastPositionId=resumeFromLastPositionId,
        )
    )

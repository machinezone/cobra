'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging
from typing import Dict

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
from cobras.common.apps_config import PUBSUB_APPKEY, getDefaultPort
from cobras.common.throttle import Throttle

DEFAULT_URL = f'ws://127.0.0.1:{getDefaultPort()}/v2?appkey={PUBSUB_APPKEY}'


class MessageHandlerClass:
    def __init__(self, connection, args):
        self.cnt = 0
        self.cntPerSec = 0
        self.throttle = Throttle(seconds=1)
        self.args = args

    async def on_init(self):
        memoryDebugger = MemoryDebugger(noTraceMalloc=True)
        self.memoryDebuggerTask = asyncio.create_task(memoryDebugger.run())
        addTaskCleanup(self.memoryDebuggerTask)

    async def handleMsg(self, message: Dict, position: str) -> ActionFlow:
        self.cnt += 1
        self.cntPerSec += 1

        logging.info(f'{message} at position {position}')

        if self.throttle.exceedRate():
            return ActionFlow.CONTINUE

        print(f"position {position} #messages {self.cnt} msg/s {self.cntPerSec}")
        self.cntPerSec = 0

        if self.args['resume_from_last_position']:
            return ActionFlow.SAVE_POSITION

        return ActionFlow.CONTINUE


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('pubsub'))
@click.option('--secret', default=getDefaultSecretForApp('pubsub'))
@click.option('--channel', default='sms_republished_v1_neo')
@click.option('--position')
@click.option('--stream_sql')
@click.option('--resume_from_last_position', is_flag=True)
def subscribe(
    url, role, secret, channel, position, stream_sql, resume_from_last_position
):
    '''Subscribe to a channel
    '''

    credentials = createCredentials(role, secret)

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

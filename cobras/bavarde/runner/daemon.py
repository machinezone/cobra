'''Chat daemon, to get notifications when messages are received

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import functools
import getpass
import asyncio
from typing import Dict, List

from daemonize import Daemonize
from klaxon import klaxon
import click

from cobras.client.client import subscribeClient
from cobras.client.credentials import createCredentials
from cobras.client.connection import ActionFlow
from cobras.common.task_cleanup import addTaskCleanup

from cobras.bavarde.client.client import (
    DEFAULT_LOCAL_URL,
    DEFAULT_URL,
    DEFAULT_ROLE,
    DEFAULT_SECRET,
)

DEFAULT_PID = "/tmp/test.pid"


class MessageHandlerClass:
    def __init__(self, connection, args):
        args['connection'] = connection

    async def on_init(self):
        '''Get a connection to the DB'''
        print('Ready to receive messages')

    async def handleMsg(self, messages: List[Dict], position: str) -> ActionFlow:
        for msg in messages:
            data = msg.get('data', {})
            user = data.get('user', 'unknown user')
            text = data.get('text', '<invalid message>')

            # We could extract a time and from the message too
            # We could display a channel

            klaxon(
                title=f'New message from Bavarde',  # App name ?
                subtitle=f'From {user}',
                message=text,
            )

        return ActionFlow.CONTINUE


async def runSubscriber(url, credentials, channel, position):
    stream_sql = None
    args = {}

    task = asyncio.create_task(
        subscribeClient(
            url, credentials, channel, position, stream_sql, MessageHandlerClass, args
        )
    )
    addTaskCleanup(task)

    await task


# FIXME username is ignored right now
def main(url, role, secret, channel, position, username):
    credentials = createCredentials(role, secret)
    asyncio.run(runSubscriber(url, credentials, channel, position))


@click.command()
@click.option('--pidfile', '-p', default=DEFAULT_PID)
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', envvar='BAVARDE_DEFAULT_ROLE', default=DEFAULT_ROLE)
@click.option(
    '--secret', envvar='BAVARDE_DEFAULT_SECRET', default=DEFAULT_SECRET, required=True
)
@click.option('--channel', envvar='BAVARDE_DEFAULT_CHANNEL', default='lobby')
@click.option('--position', default='$')
@click.option('--username', default=getpass.getuser())
@click.option('--dev', '-v', count=True)
@click.option('--foreground', '-f', is_flag=True)
def daemon(pidfile, url, role, secret, channel, position, username, dev, foreground):
    '''Chat daemon, to get notifications when messages are received'''

    click.secho(f'Kill me with kill -9 `cat {pidfile}`', fg='cyan')

    if dev:
        url = DEFAULT_LOCAL_URL

    handler = functools.partial(
        main,
        url=url,
        role=role,
        secret=secret,
        channel=channel,
        position=position,
        username=username,
    )

    # Use foreground mode for testing
    d = Daemonize(app="test_app", pid=pidfile, action=handler, foreground=foreground)
    d.start()

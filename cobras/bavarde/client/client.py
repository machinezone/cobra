'''Chat client

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.

Lot of code borrowed from websockets cli.
'''

import asyncio
import datetime
import os
import signal
import sys
import uuid
from typing import Any, Set

import click
import websockets

from cobras.client.client import subscribeClient
from cobras.client.connection import ActionFlow
from cobras.client.credentials import createCredentials
from cobras.common.task_cleanup import addTaskCleanup


def exit_from_event_loop_thread(
    loop: asyncio.AbstractEventLoop, stop: "asyncio.Future[None]"
) -> None:
    loop.stop()
    if not stop.done():
        # When exiting the thread that runs the event loop, raise
        # KeyboardInterrupt in the main thread to exit the program.
        try:
            ctrl_c = signal.CTRL_C_EVENT  # Windows
        except AttributeError:
            ctrl_c = signal.SIGINT  # POSIX
        os.kill(os.getpid(), ctrl_c)


def print_during_input(string: str) -> None:
    sys.stdout.write(
        # Save cursor position
        "\N{ESC}7"
        # Add a new line
        "\N{LINE FEED}"
        # Move cursor up
        "\N{ESC}[A"
        # Insert blank line, scroll last line down
        "\N{ESC}[L"
        # Print string in the inserted blank line
        f"{string}\N{LINE FEED}"
        # Restore cursor position
        "\N{ESC}8"
        # Move cursor down
        "\N{ESC}[B"
    )
    sys.stdout.flush()


def print_over_input(string: str) -> None:
    sys.stdout.write(
        # Move cursor to beginning of line
        "\N{CARRIAGE RETURN}"
        # Delete current line
        "\N{ESC}[K"
        # Print string
        f"{string}\N{LINE FEED}"
    )
    sys.stdout.flush()


def colorize(name):
    colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan']
    idx = hash(name) % len(colors)
    color = colors[idx]
    return click.style(name, fg=color)


class MessageHandlerClass:
    def __init__(self, connection, args):
        self.verbose = args['verbose']
        self.q = args['queue']

        args['connection'] = connection

    async def on_init(self):
        '''Get a connection to the DB'''
        print('Ready to receive messages')

    async def handleMsg(self, message: dict, position: str) -> ActionFlow:
        self.q.put_nowait((message, position))
        return ActionFlow.CONTINUE


async def runClient(
    url,
    role,
    secret,
    channel,
    position,
    stream_sql,
    verbose,
    username,
    loop,
    inputs,
    stop,
):
    credentials = createCredentials(role, secret)

    q: asyncio.Queue[str] = asyncio.Queue(loop=loop)

    args = {'verbose': verbose, 'queue': q}

    task = asyncio.create_task(
        subscribeClient(
            url, credentials, channel, position, stream_sql, MessageHandlerClass, args
        )
    )
    addTaskCleanup(task)

    try:
        while True:
            incoming: asyncio.Future[Any] = asyncio.ensure_future(q.get())
            outgoing: asyncio.Future[Any] = asyncio.ensure_future(inputs.get())
            done: Set[asyncio.Future[Any]]
            pending: Set[asyncio.Future[Any]]
            done, pending = await asyncio.wait(
                [incoming, outgoing, stop], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks to avoid leaking them.
            if incoming in pending:
                incoming.cancel()
            if outgoing in pending:
                outgoing.cancel()

            if incoming in done:
                try:
                    (message, position) = incoming.result()
                except websockets.exceptions.ConnectionClosed:
                    break
                else:
                    data = message.get('data', {})
                    user = data.get('user', 'unknown user')
                    text = data.get('text', '<invalid message>')
                    messageId = message.get('id')

                    # Use redis position to get a datetime
                    timestamp = position.split('-')[0]
                    dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000)
                    dtFormatted = dt.strftime('[%H:%M:%S]')

                    maxUserNameLength = 12
                    padding = (maxUserNameLength - len(user)) * ' '

                    user = colorize(user)
                    print_during_input(f'{dtFormatted} {padding} {user}: {text}')

            if outgoing in done:
                text = outgoing.result()

                messageId = uuid.uuid4().hex  # FIXME needed ?

                message = {'data': {'user': username, 'text': text}, 'id': messageId}

                await args['connection'].publish(channel, message)

            if stop in done:
                break

    finally:
        connection = args.get('connection')
        if connection is not None:
            closeStatus = await args['connection'].close()
            print_over_input(f"Connection closed: {closeStatus}.")

        task.cancel()
        await task

        exit_from_event_loop_thread(loop, stop)

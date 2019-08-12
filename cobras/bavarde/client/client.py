'''Chat client

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.

Lot of code borrowed from websockets cli.
'''

import asyncio
import datetime
import json
import os
import pprint
import signal
import sys
import threading
import uuid
import datetime
from typing import Any, Set

import click
import websockets
from websockets.exceptions import format_close

from cobras.client.client import subscribeClient
from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                       getDefaultSecretForApp)
from cobras.common.throttle import Throttle


def exit_from_event_loop_thread(loop: asyncio.AbstractEventLoop,
                                stop: "asyncio.Future[None]") -> None:
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
        "\N{ESC}[B")
    sys.stdout.flush()


def print_over_input(string: str) -> None:
    sys.stdout.write(
        # Move cursor to beginning of line
        "\N{CARRIAGE RETURN}"
        # Delete current line
        "\N{ESC}[K"
        # Print string
        f"{string}\N{LINE FEED}")
    sys.stdout.flush()


class MessageHandlerClass:
    def __init__(self, websockets, args):
        self.verbose = args['verbose']
        self.q = args['queue']

        args['websocket'] = websockets

    async def on_init(self):
        '''Get a connection to the DB'''
        print('Ready to receive messages')

    async def handleMsg(self, msg: str) -> bool:
        data = json.loads(msg)
        message = data['body']['messages'][0]
        position = data['body']['position']

        if isinstance(message, dict):
            self.q.put_nowait((message, position))

        return True


async def publish(websocket, msg, channel):
    publishPdu = {
        "action": "rtm/publish",
        "body": {
            "channel": channel,
            "message": msg
        }
    }

    data = json.dumps(publishPdu)
    await websocket.send(data)


async def runClient(url, role, secret, channel, position, stream_sql, verbose,
                    username, loop, inputs, stop):
    '''
    Things to do: uvloop
    '''

    credentials = createCredentials(role, secret)
    sentMessages = set()

    q: asyncio.Queue[str] = asyncio.Queue(loop=loop)

    args = {'verbose': verbose, 'queue': q}

    task = asyncio.create_task(
        subscribeClient(url, credentials, channel, position, stream_sql,
                        MessageHandlerClass, args))

    try:
        while True:
            incoming: asyncio.Future[Any] = asyncio.ensure_future(q.get())
            outgoing: asyncio.Future[Any] = asyncio.ensure_future(inputs.get())
            done: Set[asyncio.Future[Any]]
            pending: Set[asyncio.Future[Any]]
            done, pending = await asyncio.wait(
                [incoming, outgoing, stop],
                return_when=asyncio.FIRST_COMPLETED)

            # Cancel pending tasks to avoid leaking them.
            if incoming in pending:
                incoming.cancel()
            if outgoing in pending:
                outgoing.cancel()

            if incoming in done:
                try:
                    (message, position) = incoming.result()
                except websockets.ConnectionClosed:
                    break
                else:
                    data = message.get('data', {})
                    user = data.get('user', 'unknown user')
                    text = data.get('text', '<invalid message>')
                    messageId = message.get('id')

                    # breakpoint()
                    timestamp = position.split('-')[0]
                    dt = datetime.datetime.fromtimestamp(int(timestamp) / 1000)
                    dtFormatted = dt.strftime('[%H:%M:%S]')

                    if messageId not in sentMessages:
                        print_during_input(f'{dtFormatted} {user}: {text}')

            if outgoing in done:
                text = outgoing.result()

                messageId = uuid.uuid4().hex
                sentMessages.add(messageId)

                message = {
                    'data': {
                        'user': username,
                        'text': text
                    },
                    'id': messageId
                }

                await publish(args['websocket'], message, channel)

            if stop in done:
                break

    finally:
        await args['websocket'].close()
        close_status = format_close(args['websocket'].close_code,
                                    args['websocket'].close_reason)

        print_over_input(f"Connection closed: {close_status}.")

        task.cancel()
        await task

        exit_from_event_loop_thread(loop, stop)

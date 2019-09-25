'''Chat client

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.

Lot of code borrowed from websockets cli.
'''

import asyncio
import getpass
import os
import pprint
import threading
import sys

import click

from cobras.bavarde.client.client import runClient

DEFAULT_LOCAL_URL = 'ws://127.0.0.1:8765/v2?appkey=_pubsub'
DEFAULT_URL = 'ws://jeanserge.com/v2?appkey=_pubsub'

DEFAULT_ROLE = 'pubsub'
DEFAULT_SECRET = 'ccc02DE4Ed8CAB9aEfC8De3e13BfBE5E'


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', envvar='BAVARDE_DEFAULT_ROLE', default=DEFAULT_ROLE)
@click.option(
    '--secret', envvar='BAVARDE_DEFAULT_SECRET', default=DEFAULT_SECRET, required=True
)
@click.option('--channel', envvar='BAVARDE_DEFAULT_CHANNEL', default='lobby')
@click.option('--position', default='0-0')
@click.option('--username', default=getpass.getuser())
@click.option('--verbose', '-v', count=True)
@click.option('--dev', '-v', count=True)
@click.option('--stream_sql')
def client(url, role, secret, channel, position, username, stream_sql, verbose, dev):
    '''WRITEME'''
    if os.getenv('DEBUG') is not None or verbose:
        pprint.pprint(locals())

    try:
        import readline  # noqa
    except ImportError:  # Windows has no `readline` normally
        pass

    if dev:
        url = DEFAULT_LOCAL_URL

    # Create an event loop that will run in a background thread.
    loop = asyncio.new_event_loop()

    # Create a queue of user inputs. There's no need to limit its size.
    inputs: asyncio.Queue[str] = asyncio.Queue(loop=loop)

    # Create a stop condition when receiving SIGINT or SIGTERM.
    stop: asyncio.Future[None] = loop.create_future()

    # Schedule the task that will manage the connection.
    asyncio.ensure_future(
        runClient(
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
        ),
        loop=loop,
    )

    # Start the event loop in a background thread.
    thread = threading.Thread(target=loop.run_forever)
    thread.start()

    # Read from stdin in the main thread in order to receive signals.
    try:
        while True:
            message = input('> ')

            # Erase that line we just typed. FIXME: handle multi-lines inputs
            sys.stdout.write(
                # Move cursor up
                "\N{ESC}[A"
                # Move cursor to beginning of line
                "\N{CARRIAGE RETURN}"
                # Delete current line
                "\N{ESC}[K"
            )

            # Since there's no size limit, put_nowait is identical to put.
            loop.call_soon_threadsafe(inputs.put_nowait, message)
    except (KeyboardInterrupt, EOFError):  # ^C, ^D
        loop.call_soon_threadsafe(stop.set_result, None)

    # Wait for the event loop to terminate.
    thread.join()

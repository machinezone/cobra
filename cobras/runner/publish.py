'''Publish to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import datetime
import functools
import json
import os
import random
import tarfile
import uuid

import click
import uvloop

from cobras.client.client import client
from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                      getDefaultSecretForApp)
from cobras.client.publish import computeEventTimeDeltas
from cobras.common.apps_config import PUBSUB_APPKEY
from cobras.common.superuser import preventRootUsage

root = os.path.dirname(os.path.realpath(__file__))
dataDir = os.path.join(root, '..', 'data')
DEFAULT_PATH = os.path.join(dataDir, 'publish.jsonl')
DEFAULT_BATCH_PATH = os.path.join(dataDir, 'niso_events.tar.bz')


# Default channel when pushing from redis
DEFAULT_CHANNEL = 'sms_republished_v1_neo'

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={PUBSUB_APPKEY}'


async def sendEvent(websocket, channel, event, connectionId, verbose):
    data = json.loads(event)
    action = data.get('action')

    if action is None or action != 'rtm/publish':
        publishPdu = {
            "action": "rtm/publish",
            "body": {
                "channel": channel,
                "message": data
            }
        }
        line = json.dumps(publishPdu)
    else:
        data['body']['channel'] = channel
        line = json.dumps(data)

    if verbose:
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"[{now}][{connectionId}] > {line}")

    # await websocket.send(line.encode('utf8'))
    await websocket.send(line)


async def clientCallback(websocket, **args):
    item = args['item']
    channel = args['channel']
    verbose = args['verbose']
    delay = args['delay']
    repeat = args['repeat']

    if not item:  # FIXME: how can this happen ?
        return

    while True:
        connectionId = uuid.uuid4().hex[:8]
        eventsWithDeltas = computeEventTimeDeltas(item)

        N = len(eventsWithDeltas)
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"[{now}][{connectionId}] {N} events")

        for event, deltaMs in eventsWithDeltas:
            await sendEvent(websocket, channel, event, connectionId, verbose)

            if deltaMs != 0:
                print(f'sleeping for {deltaMs} ms')
                await asyncio.sleep(deltaMs / 1000)
            elif delay:
                print(f'sleeping for {delay} ms')
                await asyncio.sleep(delay)

        if not repeat:
            break


async def publishTask(url, credentials, items, channel,
                      verbose, repeat, delay):
    tasks = []
    for item in items:
        publishClientCallback = functools.partial(clientCallback,
                                                  item=item,
                                                  channel=channel,
                                                  verbose=verbose,
                                                  repeat=repeat,
                                                  delay=delay)

        task = asyncio.ensure_future(
            client(url, credentials, publishClientCallback))
        tasks.append(task)

    done, pending = await asyncio.wait(
        tasks,
        return_when=asyncio.ALL_COMPLETED,
    )
    for task in pending:
        task.cancel()


def buildItemList(path, limit):
    if tarfile.is_tarfile(path):
        items = []
        with tarfile.open(path, 'r:*') as tar:
            print('Extracting tarball...')
            members = tar.getmembers()
            for i, member in enumerate(members):
                if member.isfile():
                    f = tar.extractfile(member.name)
                    items.append(f.read().decode('utf-8'))

                if i > limit:
                    break

        # Randomize those input files
        random.shuffle(items)
    else:
        with open(path) as f:
            item = f.read()
        items = [item]

    return items


def run(url, channel, path, credentials, verbose, repeat, delay, limit):
    items = buildItemList(path, limit)
    if len(items) == 0:
        print('Empty input file')
        return

    print(f'Processing {len(items)} items')

    asyncio.get_event_loop().run_until_complete(
        publishTask(url, credentials, items, channel, verbose, repeat, delay))


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--channel', default=DEFAULT_CHANNEL)
@click.option('--path', default=DEFAULT_PATH)
@click.option('--role', default=getDefaultRoleForApp('pubsub'))
@click.option('--secret', default=getDefaultSecretForApp('pubsub'))
@click.option('--verbose', is_flag=True)
@click.option('--repeat', is_flag=True)
@click.option('--batch', is_flag=True)
@click.option('--batch_events_path', envvar='COBRA_PUBLISH_BATCH_EVENTS_PATH',
              help='An archive (tar.gz, etc...) of events files')
@click.option('--limit', default=256)
@click.option('--delay', default=0.1)
def publish(url, channel, path, role, secret, batch, batch_events_path,
            limit, verbose, repeat, delay):
    '''Publish to a channel
    '''

    preventRootUsage()
    uvloop.install()

    if batch:
        path = batch_events_path

    credentials = createCredentials(role, secret)

    run(url, channel, path, credentials, verbose, repeat, delay, limit)

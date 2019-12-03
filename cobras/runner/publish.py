'''Publish to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import datetime
import functools
import rapidjson as json
import logging
import os
import random
import tarfile
import uuid

import click
from cobras.client.client import client
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.client.publish import computeEventTimeDeltas
from cobras.common.apps_config import PUBSUB_APPKEY, getDefaultEndpoint, makeUrl
from cobras.common.throttle import Throttle

root = os.path.dirname(os.path.realpath(__file__))
dataDir = os.path.join(root, '..', 'data')
DEFAULT_PATH = os.path.join(dataDir, 'publish.jsonl')
DEFAULT_BATCH_PATH = os.path.join(dataDir, 'niso_events.tar.bz')

# Default channel when pushing from redis
DEFAULT_CHANNEL = 'sms_republished_v1_neo'


async def sendEvent(connection, channel, event, connectionId):
    data = json.loads(event)

    now = datetime.datetime.now().strftime("%H:%M:%S.%f")
    logging.info(f"[{now}][{connectionId}] > {event}")

    await connection.publish(channel, data)


async def clientCallback(connection, **args):
    item = args['item']
    channel = args['channel']
    delay = args['delay']
    repeat = args['repeat']
    summary = args['summary']

    if not item:  # FIXME: how can this happen ?
        return

    throttle = Throttle(seconds=1)
    cnt = 0

    while True:
        connectionId = uuid.uuid4().hex[:8]
        eventsWithDeltas = computeEventTimeDeltas(item)

        N = len(eventsWithDeltas)
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")
        if not summary:
            print(f"[{now}][{connectionId}] {N} events")

        for event, deltaMs in eventsWithDeltas:
            await sendEvent(connection, channel, event, connectionId)

            if deltaMs != 0:
                if not summary:
                    print(f'sleeping for {deltaMs} ms')

                await asyncio.sleep(deltaMs / 1000)
            elif delay:
                if not summary:
                    print(f'sleeping for {delay} ms')

                await asyncio.sleep(delay)

        if not repeat:
            break

        if summary:
            cnt += 1
            if throttle.exceedRate():
                continue

            print(f'{cnt} message(s) sent per second')
            cnt = 0


async def publishTask(url, credentials, items, channel, repeat, delay, summary):
    tasks = []
    for item in items:
        publishClientCallback = functools.partial(
            clientCallback,
            item=item,
            channel=channel,
            repeat=repeat,
            delay=delay,
            summary=summary,
        )

        task = asyncio.ensure_future(client(url, credentials, publishClientCallback))
        tasks.append(task)

    done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
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


def run(url, channel, path, credentials, repeat, delay, limit, summary):
    items = buildItemList(path, limit)
    if len(items) == 0:
        print('Empty input file')
        return

    print(f'Processing {len(items)} items')

    asyncio.get_event_loop().run_until_complete(
        publishTask(url, credentials, items, channel, repeat, delay, summary)
    )


@click.command()
@click.option('--endpoint', default=getDefaultEndpoint())
@click.option('--appkey', default=PUBSUB_APPKEY)
@click.option('--channel', default=DEFAULT_CHANNEL)
@click.option('--path', default=DEFAULT_PATH)
@click.option('--rolename', default=getDefaultRoleForApp('pubsub'))
@click.option('--rolesecret', default=getDefaultSecretForApp('pubsub'))
@click.option('--repeat', is_flag=True)
@click.option('--batch', is_flag=True)
@click.option('--summary', is_flag=True)
@click.option(
    '--batch_events_path',
    envvar='COBRA_PUBLISH_BATCH_EVENTS_PATH',
    help='An archive (tar.gz, etc...) of events files',
)
@click.option('--limit', default=256)
@click.option('--delay', default=0.1)
def publish(
    endpoint,
    appkey,
    channel,
    path,
    rolename,
    rolesecret,
    batch,
    batch_events_path,
    limit,
    repeat,
    delay,
    summary,
):
    '''Publish to a channel
    '''
    if batch:
        path = batch_events_path

    url = makeUrl(endpoint, appkey)
    credentials = createCredentials(rolename, rolesecret)

    run(url, channel, path, credentials, repeat, delay, limit, summary)

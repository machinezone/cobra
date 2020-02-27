'''Keyspace analyzer, used for resharding

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import collections
import csv
import sys
from rcc.client import RedisClient


# FIXME: make this a utility
def makeClientfromNode(node):
    url = f'redis://{node.ip}:{node.port}'
    return RedisClient(url, '')  # FIXME password


async def analyzeKeyspace(redisUrl: str, timeout: int):
    pattern = '__key*__:*'

    redisClient = RedisClient(redisUrl, '')
    await redisClient.connect()

    clients = []
    if redisClient.cluster:
        nodes = await redisClient.cluster_nodes()
        for node in nodes:
            client = makeClientfromNode(node)
            clients.append(client)
    else:
        clients = [redisClient]

    cmds = 'xadd'
    keyspaceConfig = 'KEAt'

    async def cb(obj, message):
        sys.stderr.write('.')
        sys.stderr.flush()

        msg = message[2].decode()
        _, _, cmd = msg.partition(':')

        if cmd in cmds:
            key = message[3].decode()
            obj[key] += 1

    tasks = []

    obj = collections.defaultdict(int)

    # First we need to make sure keyspace notifications are ON
    # Do this manually with redis-cli -p 10000 config set notify-keyspace-events KEAt
    confs = []
    for client in clients:
        conf = await client.send('CONFIG', 'GET', 'notify-keyspace-events')
        if conf[1]:
            print(f'{client} current keyspace config: {conf[1].decode()}')
            confs.append(conf[1].decode())

        # Set the new conf
        await client.send('CONFIG', 'SET', 'notify-keyspace-events', keyspaceConfig)

    try:
        for client in clients:
            task = asyncio.create_task(client.psubscribe(pattern, cb, obj))
            tasks.append(task)

        # Monitor during X seconds
        await asyncio.sleep(timeout)

        for task in tasks:
            # Cancel the tasks
            task.cancel()
            await task

    finally:
        # Now restore the notification
        for client, conf in zip(clients, confs):
            # reset the previous conf
            print(f'resetting old config {conf}')
            await client.send('CONFIG', 'SET', 'notify-keyspace-events', conf)

    print()
    plural = 's' if len(obj) > 1 else ''
    print(f'Got notifications for {len(obj)} key{plural} access')

    return obj


def writeWeightsToCsv(weights: dict, path: str):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        for key, weight in sorted(weights.items()):
            writer.writerow([key, weight])

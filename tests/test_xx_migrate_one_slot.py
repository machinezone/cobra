'''Test resharding and capturing keyspace information.
Needs to be run last hence the weid name with zzz

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os
import tempfile

from rcc.cluster.init_cluster import runNewCluster
from rcc.cluster.reshard import makeClientfromNode, waitForClusterViewToBeConsistent
from rcc.cluster.info import getClusterSignature
from rcc.cluster.reshard import migrateSlot

from test_utils import makeClient


async def runRedisCliClusterCheck(port):
    cmd = f'redis-cli --cluster check localhost:{port}'

    proc = await asyncio.create_subprocess_shell(cmd)
    stdout, stderr = await proc.communicate()


async def coro():
    root = tempfile.mkdtemp()
    clusterReadyFile = os.path.join(root, 'redis_cluster_ready')
    startPort = 12000
    redisUrl = f'redis://localhost:{startPort}'
    task = asyncio.create_task(runNewCluster(root, startPort, size=3))

    # Wait until cluster is initialized
    while not os.path.exists(clusterReadyFile):
        await asyncio.sleep(0.1)

    client = makeClient(startPort)

    i = 2
    channel = 'channel_2'
    value = f'val_{i}'
    streamId = await client.send(
        'XADD', channel, 'MAXLEN', '~', '1', b'*', 'foo', value
    )
    assert streamId is not None

    # Validate that we can read back what we wrote
    channel = 'channel_2'
    results = await client.send('XREAD', 'BLOCK', b'0', b'STREAMS', channel, '0-0')
    results = results[channel.encode()]
    # extract value
    val = results[0][1][b'foo'].decode()
    value = f'val_{i}'
    assert val == value

    signature, balanced, fullCoverage = await getClusterSignature(redisUrl)
    assert balanced
    assert fullCoverage

    # ret = await binPackingReshardCoroutine(redisUrl, weights, timeout=15)
    # assert ret
    slot = 1978
    nodes = await client.cluster_nodes()
    masterNodes = [node for node in nodes if node.role == 'master']
    masterClients = [makeClientfromNode(node) for node in masterNodes]
    sourceNode = masterNodes[0]
    destinationNode = masterNodes[1]
    await migrateSlot(masterClients, slot, sourceNode, destinationNode, dry=False)

    consistent = await waitForClusterViewToBeConsistent(redisUrl, timeout=5)
    assert consistent

    newSignature, balanced, fullCoverage = await getClusterSignature(redisUrl)
    assert signature != newSignature
    assert balanced
    assert fullCoverage

    # Now run cluster check
    await runRedisCliClusterCheck(startPort)

    # Validate that we can read back what we wrote, after resharding
    # breakpoint()

    channel = 'channel_2'
    results = await client.send('XREAD', 'BLOCK', b'0', b'STREAMS', channel, '0-0')
    results = results[channel.encode()]
    # extract value
    val = results[0][1][b'foo'].decode()
    value = f'val_{i}'
    assert val == value

    task.cancel()


def test_migrate_one_slot():
    asyncio.run(coro())

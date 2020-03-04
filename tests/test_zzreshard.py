'''Test resharding and capturing keyspace information.
Needs to be run last hence the weid name with zzz

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os
import tempfile
import uuid

from rcc.cluster.init_cluster import runNewCluster
from rcc.cluster.keyspace_analyzer import analyzeKeyspace
from rcc.cluster.reshard import binPackingReshardCoroutine
from rcc.cluster.info import getClusterSignature

from test_utils import makeClient


async def checkStrings(client):
    await client.connect()

    key = str(uuid.uuid4())
    value = str(uuid.uuid4())
    await client.send('SET', key, value)

    result = await client.send('EXISTS', key)
    assert result

    res = await client.send('GET', key)
    assert res.decode() == value

    # delete the key
    await client.send('DEL', key)
    exists = await client.send('EXISTS', key)
    assert not exists


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
    await checkStrings(client)

    # now analyze keyspace for 3 seconds
    task = asyncio.create_task(analyzeKeyspace(redisUrl, 3))

    # wait a tiny bit so that the analyzer is ready
    # (it needs to make a couple of pubsub subscriptions)
    await asyncio.sleep(0.1)

    # Write once
    for i in range(100):
        for j in range(i):
            channel = f'channel_{i}'
            value = f'val_{i}'
            streamId = await client.send(
                'XADD', channel, 'MAXLEN', '~', '1', b'*', 'foo', value
            )
            assert streamId is not None

    # Validate that we can read back what we wrote
    for i in range(1, 100):
        channel = f'channel_{i}'
        results = await client.send('XREAD', 'BLOCK', b'0', b'STREAMS', channel, '0-0')
        results = results[channel.encode()]
        # extract value
        val = results[0][1][b'foo'].decode()
        value = f'val_{i}'
        assert val == value

    await task
    keySpace = task.result()
    weights = keySpace.keys

    print('weights', weights)
    signature, balanced, fullCoverage = await getClusterSignature(redisUrl)
    assert balanced
    assert fullCoverage

    ret = await binPackingReshardCoroutine(redisUrl, weights, timeout=15)
    assert ret

    newSignature, balanced, fullCoverage = await getClusterSignature(redisUrl)
    assert signature != newSignature
    assert balanced
    assert fullCoverage

    # Now run cluster check
    await runRedisCliClusterCheck(startPort)

    # Validate that we can read back what we wrote, after resharding
    for i in range(1, 100):
        channel = f'channel_{i}'
        results = await client.send('XREAD', 'BLOCK', b'0', b'STREAMS', channel, '0-0')
        results = results[channel.encode()]
        # extract value
        val = results[0][1][b'foo'].decode()
        value = f'val_{i}'
        assert val == value

    # Do another reshard. This one should be a no-op
    # This should return statistics about the resharding
    await binPackingReshardCoroutine(redisUrl, weights, timeout=15)


def test_reshard():
    asyncio.run(coro())

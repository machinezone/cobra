'''Test hitting a disconnected server

XXX We should test multiple commands + cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import random

import pytest
from test_utils import makeClient


@pytest.fixture()
def client():
    port = random.randint(1000, 9000)
    cli = makeClient(port=port)
    yield cli


# async def info(client):
#     await client.connect()
#     info = await client.send('INFO')
#     assert len(info) > 20
#     assert 'redis_version' in info


# def test_info(client):
#    asyncio.get_event_loop().run_until_complete(info(client))

# Start redis server at a given port
async def runRedisServer(port):
    cmd = f'redis-server --port {port}'

    try:
        proc = await asyncio.create_subprocess_shell(cmd)
        stdout, stderr = await proc.communicate()
    finally:
        proc.terminate()


async def ping(client):
    port = client.port

    redisServerTask = asyncio.create_task(runRedisServer(port))
    await asyncio.sleep(0.1)  # wait a bit until the server is running

    pong = await client.send('PING')
    assert pong
    assert client.connected()

    # Now cancel the server and wait a bit (do we need this ?)
    redisServerTask.cancel()

    await asyncio.sleep(0.1)  # wait a bit until the server is not running

    with pytest.raises(OSError):
        pong = await client.send('PING')

    assert not client.connected()


def test_ping(client):
    asyncio.get_event_loop().run_until_complete(ping(client))

'''Test hitting a disconnected server

XXX We should test multiple commands + cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import random

import pytest
from test_utils import makeClient, runRedisServer


@pytest.fixture()
def client():
    port = random.randint(1000, 9000)
    cli = makeClient(port=port)
    yield cli


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

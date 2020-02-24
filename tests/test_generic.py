'''Generic test file

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import pytest
from test_utils import makeClient


@pytest.fixture()
def client():
    cli = makeClient()
    yield cli


async def info(client):
    await client.connect()
    info = await client.send('INFO')
    assert len(info) > 20
    assert 'redis_version' in info


async def ping(client):
    await client.connect()
    pong = await client.send('PING')
    assert pong


def test_info(client):
    asyncio.get_event_loop().run_until_complete(info(client))


def test_ping(client):
    asyncio.get_event_loop().run_until_complete(ping(client))

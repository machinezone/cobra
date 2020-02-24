'''Strings test file

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import uuid
import pytest
from test_utils import makeClient


@pytest.fixture()
def client():
    cli = makeClient()
    yield cli


async def connection(client):
    await client.connect()
    print(client)


async def strings(client):
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


def test_strings(client):
    asyncio.get_event_loop().run_until_complete(strings(client))

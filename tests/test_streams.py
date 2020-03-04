'''Stream test file

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


async def exists(client):
    await client.connect()

    key = str(uuid.uuid4())
    value = str(uuid.uuid4())
    await client.set(key, value)

    result = await client.exists(key)
    assert result

    res = await client.get(key)
    assert res.decode() == value

    # delete the key
    await client.delete(key)
    exists = await client.exists(key)
    assert not exists


async def add_and_read(client):
    await client.connect()

    channel = str(uuid.uuid4())

    for val in ['barbababababab', '{"bar": "baz"}']:
        maxLen = b'100'

        streamId = await client.send(
            'XADD', channel, 'MAXLEN', '~', maxLen, b'*', 'json', val
        )
        results = await client.send('XREAD', 'BLOCK', b'0', b'STREAMS', channel, '0-0')
        results = results[channel.encode()]
        assert len(results) == 1

        result = results[0]
        lastId = result[0]
        msg = result[1]
        data = msg[b'json']

        assert data == val.encode()
        assert streamId == lastId

        # simple XINFO test / we should return a nice dictionnary
        result = await client.send('XINFO', 'STREAM', channel)
        assert result[1] == 1

        # test exists
        exists = await client.send('EXISTS', channel)
        assert exists

        # delete the key
        await client.send('DEL', channel)
        exists = await client.send('EXISTS', channel)
        assert not exists


def test_connection(client):
    asyncio.get_event_loop().run_until_complete(connection(client))


def test_something(client):
    asyncio.get_event_loop().run_until_complete(add_and_read(client))

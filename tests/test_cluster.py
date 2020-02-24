'''Cluster test file

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import pytest
from test_utils import makeClient


@pytest.fixture()
def client():
    cli = makeClient()
    yield cli


async def connection(client):
    await client.connect()

    if client.cluster:
        nodes = await client.cluster_nodes()
        assert len(nodes) == 8


def test_connection(client):
    asyncio.get_event_loop().run_until_complete(connection(client))

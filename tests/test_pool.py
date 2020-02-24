'''Pool test file

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
from rcc.pool import ConnectionPool


async def pool():
    pool = ConnectionPool()
    connection = pool.get('redis://localhost')
    await connection.connect()


def test_generic():
    asyncio.get_event_loop().run_until_complete(pool())

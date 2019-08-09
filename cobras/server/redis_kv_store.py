'''Key Value store operations (set, get, delete),
but that are using streams for storage

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import traceback
from typing import Optional

import ujson

from cobras.server.redis_connections import RedisConnections


async def kvStoreRead(redisConnections: RedisConnections, pattern: str,
                      position: Optional[str], logger):
    # Create connection
    connection = await redisConnections.create(pattern)

    if position is None:
        # Get the last entry written to a stream
        end = '-'
        start = '+'
    else:
        start = position
        end = start

    try:
        results = await connection.xrevrange(pattern, start, end, 1)
        if len(results) == 0:
            return None

        result = results[0]
        position = result[0]
        msg = result[1]
        data = msg[b'json']

        msg = ujson.loads(data)
        msg['body']['position'] = position.decode()
        return msg

    except asyncio.CancelledError:
        logger('Cancelling redis subscription')
        raise

    except Exception as e:
        logger(e)
        logger('Generic Exception caught in {}'.format(traceback.format_exc()))

    finally:
        # When finished, close the connection.
        connection.close()

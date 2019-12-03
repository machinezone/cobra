'''Redis subscriber

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import rapidjson as json
import logging
import re
import traceback
from abc import ABC, abstractmethod
from typing import Optional

from cobras.server.redis_connections import RedisConnections

POSITION_PATTERN = re.compile('^(?P<id1>[0-9]+)-(?P<id2>[0-9]+)')


def validatePosition(position):
    if position is None or position == '$':
        return True

    return POSITION_PATTERN.match(position)


class RedisSubscriberMessageHandlerClass(ABC):
    def __init__(self, args):
        pass  # pragma: no cover

    @abstractmethod
    def log(self, msg):
        pass  # pragma: no cover

    @abstractmethod
    async def on_init(self, streamExists: bool, streamLength: int):
        pass  # pragma: no cover

    @abstractmethod
    async def handleMsg(self, msg: dict, position: str, payloadSize: int) -> bool:
        return True  # pragma: no cover


async def redisSubscriber(
    redisConnections: RedisConnections,
    stream: str,
    position: Optional[str],
    messageHandlerClass: RedisSubscriberMessageHandlerClass,  # noqa
    obj,
):
    messageHandler = messageHandlerClass(obj)

    redisHost = redisConnections.hashChannel(stream)
    logPrefix = f'subscriber[{redisHost} / {stream}]:'

    try:
        # Create connection
        connection = await redisConnections.create(stream)
    except Exception as e:
        logging.error(f"{logPrefix} cannot connect to redis {e}")
        connection = None

    # Ping the connection first
    try:
        await connection.ping()
    except Exception as e:
        logging.error(f"{logPrefix} cannot ping redis {e}")
        connection = None

    streamExists = False
    streamLength = 0

    if connection:
        # query the stream size
        try:
            streamExists = await connection.exists(stream) == 1
            if streamExists:
                results = await connection.xinfo(stream)
                streamLength = results[b'length']
        except Exception as e:
            logging.error(f"{logPrefix} cannot retreive stream metadata: {e}")
            pass

    try:
        await messageHandler.on_init(connection, streamExists, streamLength)
    except Exception as e:
        logging.error(f'{logPrefix} cannot initialize message handler: {e}')
        connection = None

    if connection is None:
        return messageHandler

    # lastId = '0-0'
    lastId = '$' if position is None else position

    try:
        # wait for incoming events.
        while True:
            results = await connection.xread([stream], timeout=0, latest_ids=[lastId])

            for result in results:
                lastId = result[1]
                msg = result[2]
                data = msg[b'json']

                payloadSize = len(data)
                msg = json.loads(data)
                ret = await messageHandler.handleMsg(msg, lastId.decode(), payloadSize)
                if not ret:
                    break

    except asyncio.CancelledError:
        messageHandler.log('Cancelling redis subscription')
        raise

    except Exception as e:
        messageHandler.log(e)
        messageHandler.log(
            '{logPrefix} Generic Exception caught in {}'.format(traceback.format_exc())
        )

    finally:
        messageHandler.log('Closing redis subscription')

        # When finished, close the connection.
        connection.close()

        return messageHandler


def runSubscriber(
    redisConnections: RedisConnections,
    channel: str,
    position: str,
    messageHandlerClass,
    obj=None,
):
    asyncio.get_event_loop().run_until_complete(
        redisSubscriber(redisConnections, channel, position, messageHandlerClass, obj)
    )

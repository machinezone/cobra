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
    async def on_init(self, streamExists: bool):
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

    streamExists = False

    if connection:
        # query the stream size
        try:
            streamExists = await connection.exists(stream)
        except Exception as e:
            logging.error(f"{logPrefix} cannot retreive stream metadata: {e}")
            pass

    try:
        await messageHandler.on_init(connection, streamExists)
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
            streams = {stream: lastId}
            results = await connection.xread(count=None, block=0, **streams)

            results = results[stream.encode()]

            for result in results:
                lastId = result[0].decode()
                msg = result[1]
                data = msg[b'json']

                assert lastId is not None

                payloadSize = len(data)
                msg = json.loads(data)
                ret = await messageHandler.handleMsg(msg, lastId, payloadSize)
                if not ret:
                    break

    except asyncio.CancelledError:
        messageHandler.log('Subscriber cancelled')

    except Exception as e:
        messageHandler.log(e)
        messageHandler.log(
            '{logPrefix} Generic Exception caught in {}'.format(traceback.format_exc())
        )

    finally:
        messageHandler.log('redis subscription stopped')

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

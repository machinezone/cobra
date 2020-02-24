'''Redis subscriber built on Streams, not PubSub

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import rapidjson as json
import logging
import re
import traceback
from abc import ABC, abstractmethod
from typing import Optional

from rcc.client import RedisClient

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
    client: RedisClient,
    stream: str,
    position: Optional[str],
    messageHandlerClass: RedisSubscriberMessageHandlerClass,  # noqa
    obj,
):
    messageHandler = messageHandlerClass(obj)

    logPrefix = f'subscriber[{stream}]: {client}'

    try:
        # Create connection
        await client.connect()
    except Exception as e:
        logging.error(f"{logPrefix} cannot connect to redis {e}")
        client = None

    # Ping the connection first
    try:
        await client.send('PING')
    except Exception as e:
        logging.error(f"{logPrefix} cannot ping redis {e}")
        client = None

    streamExists = False
    streamLength = 0

    if client:
        # query the stream size
        try:
            streamExists = await client.send('EXISTS', stream)
            if streamExists:
                results = await client.send('XINFO', 'STREAM', stream)
                streamLength = results[1]
        except Exception as e:
            logging.error(f"{logPrefix} cannot retreive stream metadata: {e}")
            pass

    try:
        await messageHandler.on_init(client, streamExists, streamLength)
    except Exception as e:
        logging.error(f'{logPrefix} cannot initialize message handler: {e}')
        client = None

    if client is None:
        return messageHandler

    # lastId = '0-0'
    lastId = '$' if position is None else position

    try:
        # wait for incoming events.
        while True:
            results = await client.send(
                'XREAD', 'BLOCK', b'0', b'STREAMS', stream, lastId
            )

            for result in results:
                lastId = result[0]
                msg = result[1]
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
        client.close()

        return messageHandler


def runSubscriber(
    client: RedisClient, channel: str, position: str, messageHandlerClass, obj=None
):
    asyncio.get_event_loop().run_until_complete(
        redisSubscriber(client, channel, position, messageHandlerClass, obj)
    )

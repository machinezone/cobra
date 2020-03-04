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
    async def on_init(self, client, streamExists: bool, streamLength: int):
        pass  # pragma: no cover

    @abstractmethod
    async def handleMsg(self, msg: dict, position: str, payloadSize: int) -> bool:
        return True  # pragma: no cover


async def redisSubscriber(
    client,
    stream: str,
    position: Optional[str],
    messageHandlerClass: RedisSubscriberMessageHandlerClass,  # noqa
    obj,
):
    messageHandler = messageHandlerClass(obj)

    logPrefix = f'subscriber[{stream}]: {client}'

    streamExists = False

    if client:
        # query the stream size
        try:
            streamExists = await client.exists(stream)
        except Exception as e:
            logging.error(f"{logPrefix} cannot retreive stream metadata: {e}")
            client = None

    try:
        await messageHandler.on_init(client, streamExists, streamLength=0)  # FIXME
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
            streams = {stream: lastId}
            results = await client.xread(streams)

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
        backtrace = traceback.format_exc()
        messageHandler.log(f'{logPrefix} Generic Exception caught in {backtrace}')

    finally:
        messageHandler.log('redis subscription stopped')

        return messageHandler

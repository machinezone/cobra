'''Redis subscriber

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import traceback
from abc import ABC, abstractmethod

import ujson

from cobras.server.redis_connections import RedisConnections


class RedisSubscriberMessageHandlerClass(ABC):
    def __init__(self, args):
        pass  # pragma: no cover

    @abstractmethod
    def log(self, msg):
        pass  # pragma: no cover

    @abstractmethod
    async def on_init(self):
        pass  # pragma: no cover

    @abstractmethod
    async def handleMsg(self, msg: dict, payloadSize: int) -> bool:
        return True  # pragma: no cover


async def redisSubscriber(redisConnections: RedisConnections,
                          pattern: str,
                          messageHandlerClass: RedisSubscriberMessageHandlerClass,  # noqa
                          obj):
    # Create connection
    connection = await redisConnections.create(pattern, useAioRedis=False)

    # Create subscriber.
    subscriber = await connection.start_subscribe()

    # Subscribe to channel.
    await subscriber.subscribe([pattern])

    messageHandler = messageHandlerClass(obj)
    await messageHandler.on_init(connection)

    try:
        # wait for incoming events.
        while True:
            reply = await subscriber.next_published()
            msg = reply.value

            payloadSize = len(msg)
            msg = ujson.loads(msg)
            ret = await messageHandler.handleMsg(msg, payloadSize)
            if not ret:
                break

    except asyncio.CancelledError:
        messageHandler.log('Cancelling redis subscription')
        raise

    except Exception as e:
        messageHandler.log(e)
        messageHandler.log(
            'Generic Exception caught in {}'.format(traceback.format_exc()))

    finally:
        messageHandler.log('Closing redis subscription')

        # When finished, close the connection.
        connection.close()


def runSubscriber(redisConnections: RedisConnections,
                  channel: str, messageHandlerClass, obj=None):
    asyncio.get_event_loop().run_until_complete(
        redisSubscriber(redisConnections, channel,
                        messageHandlerClass, obj))

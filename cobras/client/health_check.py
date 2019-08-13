'''Health check to validate that a server is ok.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import json
import uuid
from typing import Dict

from cobras.client.client import subscribeClient
from cobras.client.credentials import createCredentials
from cobras.common.apps_config import HEALTH_APPKEY


def getDefaultHealthCheckChannel():
    randomKey = uuid.uuid4().hex[:8]
    return f'sms_health_check_channel_{randomKey}'


def getDefaultHealthCheckHttpUrl(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = 8765

    return f'http://{host}:{port}/health/'


def getDefaultHealthCheckUrl(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = 8765

    return f'ws://{host}:{port}/v2?appkey={HEALTH_APPKEY}'


def healthCheck(url, role, secret, channel):
    '''Perform a health check'''
    class MessageHandlerClass:
        def __init__(self, connection, args):
            self.connection = connection
            self.channel = args['channel']
            self.content = args['content']
            self.subscriptionId = self.channel
            self.parsedMessage = None

        async def on_init(self):
            await self.connection.publish(self.channel, self.content)

        async def handleMsg(self, message: Dict, position: str) -> bool:
            self.parsedMessage = message
            return False

    credentials = createCredentials(role, secret)

    position = None
    magicNumber = 666
    refAndroidId = uuid.uuid4().hex
    content = {
        'device': {
            'game': 'test',
            'android_id': refAndroidId
        },
        'magic': magicNumber
    }

    fsqlFilter = f"""select magic,device.android_id
                     from `{channel}` where
                         device.game = 'test' AND
                         device.android_id = '{refAndroidId}' AND
                         magic = {magicNumber}
    """
    messageHandler = asyncio.get_event_loop().run_until_complete(
        subscribeClient(url, credentials, channel, position, fsqlFilter,
                        MessageHandlerClass, {
                            'channel': channel,
                            'content': content
                        }))

    message = messageHandler.parsedMessage

    if message.get('device.android_id') != refAndroidId:
        raise ValueError(f'incorrect android_id: {data}')

    if magicNumber != message['magic']:
        raise ValueError(f'incorrect magic: {data}')

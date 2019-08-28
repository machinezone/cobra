'''Health check to validate that a server is ok.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os
import urllib
import uuid
from typing import Dict

from cobras.client.client import subscribeClient, unsafeSubcribeClient
from cobras.client.connection import ActionFlow
from cobras.client.credentials import createCredentials
from cobras.common.apps_config import HEALTH_APPKEY


def getDefaultHealthCheckChannel():
    randomKey = uuid.uuid4().hex[:8]
    return f'sms_health_check_channel_{randomKey}'


def getDefaultHealthCheckHttpUrl(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = os.getenv('COBRA_PORT', 8765)

    return f'http://{host}:{port}/health/'


def getDefaultHealthCheckUrl(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = os.getenv('COBRA_PORT', 8765)

    return f'ws://{host}:{port}/v2?appkey={HEALTH_APPKEY}'


def healthCheck(url, role, secret, channel, retry=False, httpCheck=False):
    '''Perform a health check'''

    if httpCheck:
        # the first check to make is the simple HTTP one
        parsedUrl = urllib.parse.urlparse(url)
        netloc = parsedUrl.netloc
        host, _, port = netloc.partition(':')

        scheme = 'http' if parsedUrl.scheme == 'ws' else 'https'

        httpUrl = f'{scheme}://{host}:{port}/health/'
        print('url:', httpUrl)
        with urllib.request.urlopen(httpUrl) as response:
            html = response.read()
            value = html.decode('utf8')
            if value != 'OK\n':
                raise ValueError(f'Invalid http response, {value} != OK')

    class MessageHandlerClass:
        def __init__(self, connection, args):
            self.connection = connection
            self.channel = args['channel']
            self.content = args['content']
            self.subscriptionId = self.channel
            self.parsedMessage = None

        async def on_init(self):
            await self.connection.publish(self.channel, self.content)

        async def handleMsg(self, message: Dict, position: str) -> ActionFlow:
            self.parsedMessage = message
            return ActionFlow.STOP

    credentials = createCredentials(role, secret)

    position = None
    magicNumber = 666
    refAndroidId = uuid.uuid4().hex
    content = {
        'device': {'game': 'test', 'android_id': refAndroidId},
        'magic': magicNumber,
    }

    fsqlFilter = f"""select magic,device.android_id
                     from `{channel}` where
                         device.game = 'test' AND
                         device.android_id = '{refAndroidId}' AND
                         magic = {magicNumber}
    """

    messageHandlerArgs = {'channel': channel, 'content': content}

    handler = unsafeSubcribeClient
    if retry:
        handler = subscribeClient

    messageHandler = asyncio.get_event_loop().run_until_complete(
        handler(
            url,
            credentials,
            channel,
            position,
            fsqlFilter,
            MessageHandlerClass,
            messageHandlerArgs,
        )
    )

    message = messageHandler.parsedMessage

    if message.get('device.android_id') != refAndroidId:
        raise ValueError(f'incorrect android_id: {message}')

    if magicNumber != message['magic']:
        raise ValueError(f'incorrect magic: {message}')

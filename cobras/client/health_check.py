'''Health check to validate that a server is ok.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import json
import uuid

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
        def __init__(self, websocket, args):
            self.websocket = websocket
            self.channel = args['channel']
            self.content = args['content']
            self.subscriptionId = self.channel
            self.msg = None

        async def on_init(self):
            await self.publishHealthMsg()

        async def unsubscribe(self):
            # Unsubscribe
            unsubscribePdu = {
                "action": "rtm/unsubscribe",
                "body": {
                    "subscription_id": self.subscriptionId
                }
            }

            data = json.dumps(unsubscribePdu)
            print(f"> {data}")
            await self.websocket.send(data)
            await self.websocket.recv()  # needed ?

        async def publishHealthMsg(self):
            publishPdu = {
                "action": "rtm/publish",
                "body": {
                    "channel": self.channel,
                    "message": {
                        "messages": [self.content]
                    }
                }
            }

            data = json.dumps(publishPdu)
            print(f"> {data}")
            await self.websocket.send(data)

        async def handleMsg(self, msg: str) -> bool:
            print('Received', msg)
            data = json.loads(msg)

            if data.get('action') == 'rtm/publish/error':
                raise ValueError(data.get('body', {}).get('error'))

            self.parsedMessage = data

            await self.unsubscribe()

            # The server should not send this message to us
            await self.publishHealthMsg()
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
        subscribeClient(url, credentials, channel, position,
                        fsqlFilter, MessageHandlerClass,
                        {'channel': channel, 'content': content}))

    data = messageHandler.parsedMessage
    body = data['body']
    if body is None:
        raise ValueError(f'missing body: {data}')

    messages = body.get('messages')
    if messages is None:
        raise ValueError(f'missing messages: {data}')

    if not isinstance(messages, list):
        raise ValueError(f'messages is not a list: {type(messages)} {data}')

    if len(messages) == 0:
        raise ValueError(f'messages is empty: {data}')

    message = messages[0]
    if not isinstance(message, dict):
        raise ValueError(f'message is not a dict: {type(message)} {data}')

    if message.get('device.android_id') != refAndroidId:
        raise ValueError(f'incorrect android_id: {data}')

    if magicNumber != message['magic']:
        raise ValueError(f'incorrect magic: {data}')

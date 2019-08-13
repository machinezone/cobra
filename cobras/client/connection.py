'''Cobra connection

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import itertools
import json

import websockets

from cobras.common.auth_hash import computeHash


class AuthException(Exception):
    pass


class HandshakeException(Exception):
    pass


class Connection(object):
    def __init__(self, url, creds, verbose=False):
        self.url = url
        self.creds = creds
        self.idIterator = itertools.count()
        self.verbose = verbose

    async def connect(self):
        self.websocket = await websockets.connect(self.url)

        role = self.creds['role']

        handshake = {
            "action": "auth/handshake",
            "id": next(self.idIterator),
            "body": {
                "data": {
                    "role": role
                },
                "method": "role_secret"
            }
        }
        print(f"> {handshake}")
        await self.websocket.send(json.dumps(handshake))

        handshakeResponse = await self.websocket.recv()
        print(f"< {handshakeResponse}")

        response = json.loads(handshakeResponse)
        if response.get('action') != 'auth/handshake/ok':
            raise HandshakeException('Handshake error.')

        reply = json.loads(handshakeResponse)
        nonce = bytearray(reply['body']['data']['nonce'], 'utf8')

        secret = bytearray(self.creds['secret'], 'utf8')

        challenge = {
            "action": "auth/authenticate",
            "id": next(self.idIterator),
            "body": {
                "method": "role_secret",
                "credentials": {
                    "hash": computeHash(secret, nonce)
                }
            }
        }
        print(f"> {challenge}")
        await self.websocket.send(json.dumps(challenge))

        challengeResponse = await self.websocket.recv()
        print(f"< {challengeResponse}")

        response = json.loads(challengeResponse)
        if response.get('action') != 'auth/authenticate/ok':
            raise AuthException('Authentication error.')

    async def subscribe(self,
                        channel,
                        position,
                        fsqlFilter,
                        messageHandlerClass,
                        messageHandlerArgs,
                        subscriptionId):

        subscription = {
            "action": "rtm/subscribe",
            "id": next(self.idIterator),
            "body": {
                "subscription_id": subscriptionId,
                "channel": channel,
                "fast_forward": True,
                "filter": fsqlFilter
            },
        }

        if position is not None:
            subscription['body']['position'] = position

        print(f"> {subscription}")
        await self.websocket.send(json.dumps(subscription))

        subscribeResponse = await self.websocket.recv()
        print(f"< {subscribeResponse}")

        # validate response
        data = json.loads(subscribeResponse)
        if data.get('action') != 'rtm/subscribe/ok':
            raise ValueError(data.get('body', {}).get('error'))

        messageHandler = messageHandlerClass(self, messageHandlerArgs)
        await messageHandler.on_init()

        async for msg in self.websocket:
            data = json.loads(msg)
            message = data['body']['messages'][0]
            position = data['body']['position']

            ret = await messageHandler.handleMsg(message, position)
            if not ret:
                break

        try:
            await self.unsubscribe(subscriptionId)
        except websockets.exceptions.ConnectionClosed as e:
            pass

        return messageHandler

    async def unsubscribe(self, subscriptionId):
        unsubscribePdu = {
            "action": "rtm/unsubscribe",
            "id": next(self.idIterator),
            "body": {
                "subscription_id": subscriptionId
            }
        }

        data = json.dumps(unsubscribePdu)
        print(f"> {data}")
        await self.websocket.send(data)

        unsubscribeResponse = await self.websocket.recv()
        print(f"< {unsubscribeResponse}")

    async def publish(self, channel, msg):
        publishPdu = {
            "action": "rtm/publish",
            "id": next(self.idIterator),
            "body": {
                "channel": channel,
                "message": msg
            }
        }

        data = json.dumps(publishPdu)

        if self.verbose:
            print(f"> {data}")

        await self.websocket.send(data)

    async def close(self):
        await self.websocket.close()
        close_status = websockets.exceptions.format_close(self.websocket.close_code,
                                                          self.websocket.close_reason)
        return close_status


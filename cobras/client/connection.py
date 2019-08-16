'''Cobra connection

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import itertools
import json
import collections

import websockets

from cobras.common.auth_hash import computeHash


class AuthException(Exception):
    pass


class HandshakeException(Exception):
    pass


class Connection(object):
    def __init__(self, url, creds, verbose=True):
        self.url = url
        self.creds = creds
        self.idIterator = itertools.count()
        self.verbose = verbose

        # different queues per action kind or instances
        self.queues = collections.defaultdict(asyncio.Queue)

        self.task = None

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

        self.task = asyncio.create_task(self.getResponse())

    def __del__(self):
        if self.task is not None:
            self.task.cancel()

    async def getResponse(self):
        while True:
            response = await self.websocket.recv()
            if self.verbose:
                print(f'< {response}')

            data = json.loads(response)

            action = data['action']
            action = '/'.join(action.split('/')[:2])
            actionId = action + '::' + str(data['id'])

            if action == 'rtm/subscription':
                actionId = action + '::' + data['body']['subscription_id']

            q = self.getQueue(actionId)

            await q.put(data)

    def getQueue(self, action):
        q = self.queues[action]
        return q

    def computeDefaultActionId(self, pdu):
        action = pdu['action']
        actionId = f'{action}::' + str(pdu['id'])
        return actionId

    async def send(self, pdu):
        actionId = self.computeDefaultActionId(pdu)

        data = json.dumps(pdu)
        print(f"> {data}")
        await self.websocket.send(data)

        # get the response
        data = await self.getQueue(actionId).get()
        print(f"< {data}")

        # validate response
        if data.get('action') != (pdu['action'] + '/ok'):
            raise ValueError(data.get('body', {}).get('error'))

        return data

    async def subscribe(self,
                        channel,
                        position,
                        fsqlFilter,
                        messageHandlerClass,
                        messageHandlerArgs,
                        subscriptionId):
        pdu = {
            "action": "rtm/subscribe",
            "id": next(self.idIterator),
            "body": {
                "subscription_id": subscriptionId,
                "channel": channel,
                "fast_forward": True,
                "filter": fsqlFilter
            },
        }
        await self.send(pdu)

        messageHandler = messageHandlerClass(self, messageHandlerArgs)
        await messageHandler.on_init()

        actionId = 'rtm/subscription::' + subscriptionId

        while True:
            data = await self.getQueue(actionId).get()

            message = data['body']['messages'][0]
            position = data['body']['position']

            ret = await messageHandler.handleMsg(message, position)
            if not ret:
                break

        try:
            await self.unsubscribe(subscriptionId)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection is closed, cannot unsubscribe")
            pass

        return messageHandler

    async def unsubscribe(self, subscriptionId):
        pdu = {
            "action": "rtm/unsubscribe",
            "id": next(self.idIterator),
            "body": {
                "subscription_id": subscriptionId
            }
        }
        await self.send(pdu)

    async def publish(self, channel, msg):
        pdu = {
            "action": "rtm/publish",
            "id": next(self.idIterator),
            "body": {
                "channel": channel,
                "message": msg
            }
        }
        await self.send(pdu)

    async def write(self, channel, msg):
        pdu = {
            "action": "rtm/write",
            "id": next(self.idIterator),
            "body": {
                "channel": channel,
                "message": msg
            }
        }
        await self.send(pdu)

    async def read(self, channel, position=None):
        pdu = {
            "action": "rtm/read",
            "id": next(self.idIterator),
            "body": {
                "channel": channel,
            }
        }
        data = await self.send(pdu)

        msg = data['body']['message']  # FIXME data missing / error handling ?
        return msg

    async def close(self):
        await self.websocket.close()
        close_status = websockets.exceptions.format_close(self.websocket.close_code,
                                                          self.websocket.close_reason)
        return close_status


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


class ActionException(Exception):
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
        self.stop = asyncio.get_running_loop().create_future()

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        self.task = asyncio.create_task(self.waitForResponses())

        role = self.creds['role']

        handshake = {
            "action": "auth/handshake",
            "id": next(self.idIterator),
            "body": {
                "data": {
                    "role": self.creds['role']
                },
                "method": "role_secret"
            }
        }

        reply = await self.send(handshake)
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
        # print(f"> {challenge}")
        # await self.websocket.send(json.dumps(challenge))

        # challengeResponse = await self.websocket.recv()
        # print(f"< {challengeResponse}")

        # response = json.loads(challengeResponse)
        # if response.get('action') != 'auth/authenticate/ok':
        #     raise AuthException('Authentication error.')
        await self.send(challenge)

    def __del__(self):
        if self.task is not None:
            self.task.cancel()

    async def waitForResponses(self):
        try:
            while True:
                response = await self.websocket.recv()

                # if self.verbose:
                #     print(f'< {response}')

                data = json.loads(response)

                action = data['action']
                action = '/'.join(action.split('/')[:2])
                actionId = action + '::' + str(data['id'])

                if action == 'rtm/subscription':
                    actionId = action + '::' + data['body']['subscription_id']

                q = self.getQueue(actionId)

                await q.put(data)

        except Exception as e:
            print(f'unexpected exception: {e}')

            # propagate the exception to the caller
            self.stop.set_result(e)

    def getQueue(self, action):
        q = self.queues[action]
        return q

    def computeDefaultActionId(self, pdu):
        action = pdu['action']
        actionId = f'{action}::' + str(pdu['id'])
        return actionId

    async def getActionResponse(self, actionId):
        '''
        This could be as simple as:
            data = await self.getQueue(actionId).get()

        Unfortunately we need to handle exception in the 
        'fetch response coroutine' so that we can rethrow them here
        '''
        incoming = asyncio.ensure_future(self.getQueue(actionId).get())

        done, pending = await asyncio.wait(
             [incoming, self.stop],
             return_when=asyncio.FIRST_COMPLETED)

        # Cancel pending tasks to avoid leaking them.
        if incoming in pending:
            incoming.cancel()

        if incoming in done:
            data = incoming.result()
            return data

        if self.stop in done:
            # Reraise the exception which was caught in self.waitForResponses
            raise self.stop.result()

    async def send(self, pdu):
        actionId = self.computeDefaultActionId(pdu)

        data = json.dumps(pdu)
        print(f"> {data}")
        await self.websocket.send(data)

        # get the response
        data = await self.getActionResponse(actionId)
        print(f"< {data}")

        # validate response
        if data.get('action') != (pdu['action'] + '/ok'):
            raise ActionException(data.get('body', {}).get('error'))

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
            data = await self.getActionResponse(actionId)

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


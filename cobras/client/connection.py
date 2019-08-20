'''Cobra connection

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import itertools
import json
import collections
import logging
from enum import Flag, auto

import websockets

from cobras.common.auth_hash import computeHash


class AuthException(Exception):
    pass


class HandshakeException(Exception):
    pass


class ActionException(Exception):
    pass


class ActionFlow(Flag):
    CONTINUE = auto()
    STOP = auto()
    SAVE_POSITION = auto()


class Connection(object):
    '''FIXME: leaking queues
    '''
    def __init__(self, url, creds):
        self.url = url
        self.creds = creds
        self.idIterator = itertools.count()
        self.connectionId = None

        # different queues per action kind or instances
        self.queues = collections.defaultdict(asyncio.Queue)

        self.task = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        self.task = asyncio.create_task(self.waitForResponses())
        self.stop = asyncio.get_running_loop().create_future()

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

        response = await self.send(handshake)

        self.connectionId = response['body']['data']['connection_id']

        nonce = bytearray(response['body']['data']['nonce'], 'utf8')
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
        await self.send(challenge)

    def __del__(self):
        if self.task is not None:
            self.task.cancel()

    async def waitForResponses(self):
        try:
            while True:
                response = await self.websocket.recv()

                logging.debug(f'< {response}')
                data = json.loads(response)

                action = data['action']
                action = '/'.join(action.split('/')[:2])
                actionId = action + '::' + str(data['id'])

                if action == 'rtm/subscription':
                    actionId = action + '::' + data['body']['subscription_id']

                q = self.getQueue(actionId)

                await q.put(data)

        except Exception as e:
            logging.error(f'unexpected exception: {e}')

            # propagate the exception to the caller
            self.stop.set_result(e)

    def getQueue(self, action):
        q = self.queues[action]
        return q

    def deleteQueue(self, action):
        del self.queues[action]

    def computeDefaultActionId(self, pdu):
        action = pdu['action']
        actionId = f'{action}::' + str(pdu['id'])
        return actionId

    async def getActionResponse(self, actionId, retainQueue=False):
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

            if not retainQueue:
                self.deleteQueue(actionId)

            return data

        if self.stop in done:
            # Reraise the exception which was caught in self.waitForResponses
            raise self.stop.result()

    async def send(self, pdu):
        actionId = self.computeDefaultActionId(pdu)

        data = json.dumps(pdu)
        logging.info(f"> {data}")
        await self.websocket.send(data)

        # get the response
        data = await self.getActionResponse(actionId)
        logging.info(f"< {data}")

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
                        subscriptionId,
                        resumeFromLastPosition=False,
                        resumeFromLastPositionId=None):

        if resumeFromLastPosition:
            try:
                position = await self.read(resumeFromLastPositionId)
            except Exception as e:
                logging.warning('Cannot retrieve last position id for {resumeFromLastPositionId}: {e}')
                pass

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

        if position is not None:
            pdu['body']['position'] = position

        await self.send(pdu)

        messageHandler = messageHandlerClass(self, messageHandlerArgs)
        await messageHandler.on_init()

        actionId = 'rtm/subscription::' + subscriptionId

        while True:
            data = await self.getActionResponse(actionId, retainQueue=True)

            message = data['body']['messages'][0]
            position = data['body']['position']

            ret = await messageHandler.handleMsg(message, position)

            if resumeFromLastPositionId and ret == ActionFlow.SAVE_POSITION:
                await self.write(resumeFromLastPositionId, position)

            if ret == ActionFlow.STOP:
                break

        self.deleteQueue(actionId)

        try:
            await self.unsubscribe(subscriptionId)
        except websockets.exceptions.ConnectionClosed as e:
            logging.warning(f"Connection is closed, cannot unsubscribe")
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

    async def adminCloseConnection(self, connectionId):
        pdu = {
            "action": "admin/close_connection",
            "id": next(self.idIterator),
            "body": {
                "connection_id": connectionId
            }
        }
        await self.send(pdu)

    async def adminGetConnections(self):
        pdu = {
            "action": "admin/get_connections",
            "id": next(self.idIterator),
            "body": {}
        }
        data = await self.send(pdu)

        try:
            return data.get('body', {}).get('connections')
        except Exception as e:
            raise ValueError(f'rpc/admin/get_connections_count failure {e}')

    async def close(self):
        await self.websocket.close()
        close_status = websockets.exceptions.format_close(self.websocket.close_code,
                                                          self.websocket.close_reason)
        return close_status

'''Cobra connection

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import collections
import copy
import itertools
import json
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

        self.subscriptions = set()

    def __del__(self):
        if self.task is not None:
            self.task.cancel()

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        self.task = asyncio.create_task(self.waitForResponses())
        self.stop = asyncio.get_running_loop().create_future()

        role = self.creds['role']
        if role is None:
            raise ValueError('connect: Missing role')

        handshake = {
            "action": "auth/handshake",
            "body": {"data": {"role": role}, "method": "role_secret"},
        }

        response = await self.send(handshake)

        self.connectionId = response['body']['data']['connection_id']

        nonce = bytearray(response['body']['data']['nonce'], 'utf8')
        secret = bytearray(self.creds['secret'], 'utf8')

        challenge = {
            "action": "auth/authenticate",
            "body": {
                "method": "role_secret",
                "credentials": {"hash": computeHash(secret, nonce)},
            },
        }
        await self.send(challenge)

    async def waitForResponses(self):
        try:
            while True:
                response = await self.websocket.recv()

                logging.debug(f'< {response}')
                data = json.loads(response)

                msgId = data.get('id')
                if msgId is None:
                    raise ActionException('server bug: incoming message has no id')

                action = data['action']
                action = '/'.join(action.split('/')[:2])
                actionId = action + '::' + str(msgId)

                if action == 'rtm/subscription':
                    actionId = action + '::' + data['body']['subscription_id']

                q = self.getQueue(actionId)

                await q.put(data)

        except websockets.exceptions.ConnectionClosedOK as e:
            self.stop.set_result(e)

        except Exception as e:
            logging.error(f'unexpected exception: {e}')
            self.stop.set_result(e)

        finally:
            if len(self.queues) != 0:
                logging.warning(f'connection has pending queues: {self.queues}')

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
            [incoming, self.stop], return_when=asyncio.FIRST_COMPLETED
        )

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
            exception = self.stop.result()
            raise exception

    async def send(self, pdu):
        # Set the message id
        pdu["id"] = next(self.idIterator)

        # Compute the action id
        actionId = self.computeDefaultActionId(pdu)

        data = json.dumps(pdu)
        logging.info(f"client > {data}")
        await self.websocket.send(data)

        # get the response
        data = await self.getActionResponse(actionId)
        logging.info(f"client < {data}")

        # validate response
        if data.get('action') != (pdu['action'] + '/ok'):
            raise ActionException(data.get('body', {}).get('error'))

        return data

    async def subscribe(
        self,
        channel,
        position,
        fsqlFilter,
        messageHandlerClass,
        messageHandlerArgs,
        subscriptionId,
        resumeFromLastPosition=False,
        resumeFromLastPositionId=None,
    ):

        if resumeFromLastPosition:
            try:
                position = await self.read(resumeFromLastPositionId)
            except Exception as e:
                logging.warning(
                    'Cannot retrieve last position id for '
                    + f'{resumeFromLastPositionId} - Error: {e}'
                )
                pass

        pdu = {
            "action": "rtm/subscribe",
            "body": {
                "subscription_id": subscriptionId,
                "channel": channel,
                "fast_forward": True,
                "filter": fsqlFilter,
            },
        }

        if position is not None:
            pdu['body']['position'] = position

        await self.send(pdu)

        messageHandler = messageHandlerClass(self, messageHandlerArgs)
        await messageHandler.on_init()

        self.subscriptions.add(subscriptionId)

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
            logging.warning(f"Connection is closed, cannot unsubscribe: {e}")
            pass

        return messageHandler

    async def unsubscribe(self, subscriptionId):
        pdu = {"action": "rtm/unsubscribe", "body": {"subscription_id": subscriptionId}}
        await self.send(pdu)

        self.subscriptions.remove(subscriptionId)

    async def publish(self, channel, msg):
        pdu = {"action": "rtm/publish", "body": {"channel": channel, "message": msg}}
        await self.send(pdu)

    async def write(self, channel, msg):
        pdu = {"action": "rtm/write", "body": {"channel": channel, "message": msg}}
        await self.send(pdu)

    async def read(self, channel, position=None):
        pdu = {"action": "rtm/read", "body": {"channel": channel}}
        data = await self.send(pdu)

        msg = data['body']['message']  # FIXME data missing / error handling ?
        return msg

    async def delete(self, channel):
        pdu = {"action": "rtm/delete", "body": {"channel": channel}}
        await self.send(pdu)

    async def adminCloseConnection(self, connectionId):
        pdu = {
            "action": "admin/close_connection",
            "body": {"connection_id": connectionId},
        }
        await self.send(pdu)

    async def adminGetConnections(self):
        pdu = {"action": "admin/get_connections", "body": {}}
        data = await self.send(pdu)

        try:
            return data.get('body', {}).get('connections')
        except Exception as e:
            raise ValueError(f'rpc/admin/get_connections_count failure {e}')

    async def close(self):
        subscriptions = copy.copy(self.subscriptions)
        for subscription in subscriptions:
            await self.unsubscribe(subscription)

        keys = [key for key in self.queues.keys()]
        for actionId in keys:
            self.deleteQueue(actionId)

        await self.websocket.close()
        close_status = websockets.exceptions.format_close(
            self.websocket.close_code, self.websocket.close_reason
        )
        return close_status

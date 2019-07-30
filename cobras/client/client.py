'''Client for a cobra server.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import functools
import itertools
import json

import click
import websockets

from cobras.common.auth_hash import computeHash


class AuthException(Exception):
    pass


class HandshakeException(Exception):
    pass


async def clientInternal(url, creds, clientCallback):
    '''Main client. Does authenticate then invoke the clientCallback which
    takes control.
    '''

    async with websockets.connect(url) as websocket:

        idIterator = itertools.count()
        role = creds['role']

        handshake = {
            "action": "auth/handshake",
            "id": next(idIterator),
            "body": {
                "data": {
                    "role": role
                },
                "method": "role_secret"
            }
        }
        print(f"> {handshake}")
        await websocket.send(json.dumps(handshake))

        handshakeResponse = await websocket.recv()
        print(f"< {handshakeResponse}")

        response = json.loads(handshakeResponse)
        if response.get('action') != 'auth/handshake/ok':
            raise HandshakeException('Handshake error.')

        reply = json.loads(handshakeResponse)
        nonce = bytearray(reply['body']['data']['nonce'], 'utf8')

        secret = bytearray(creds['secret'], 'utf8')

        challenge = {
            "action": "auth/authenticate",
            "id": next(idIterator),
            "body": {
                "method": "role_secret",
                "credentials": {
                    "hash": computeHash(secret, nonce)
                }
            }
        }
        print(f"> {challenge}")
        await websocket.send(json.dumps(challenge))

        challengeResponse = await websocket.recv()
        print(f"< {challengeResponse}")

        response = json.loads(challengeResponse)
        if response.get('action') != 'auth/authenticate/ok':
            raise AuthException('Authentication error.')

        return await clientCallback(websocket)


async def client(url, creds, clientCallback):

    while True:
        try:
            return await clientInternal(url, creds, clientCallback)
        except TimeoutError as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass
        except ConnectionRefusedError as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass
        except ConnectionResetError as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass
        except websockets.exceptions.ConnectionClosed as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass
        except OSError as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass
        except AuthException as e:
            click.secho(str(e), fg='red')
            await asyncio.sleep(1)
            pass


async def subscribeHandler(websocket, **args):
    channel = args['channel']
    fsqlFilter = args['fsqlFilter']
    messageHandlerClass = args['messageHandlerClass']
    messageHandlerArgs = args['messageHandlerArgs']
    subscriptionId = args.get('subscription_id', channel)
    messageHandlerArgs['subscription_id'] = subscriptionId

    subscription = {
        "action": "rtm/subscribe",
        "body": {
            "subscription_id": subscriptionId,
            "channel": channel,
            "fast_forward": True,
            "filter": fsqlFilter
        },
        "id": 3  # FIXME
    }
    print(f"> {subscription}")
    await websocket.send(json.dumps(subscription))

    subscribeResponse = await websocket.recv()
    print(f"< {subscribeResponse}")

    messageHandler = messageHandlerClass(websocket, messageHandlerArgs)
    await messageHandler.on_init()

    async for msg in websocket:
        ret = await messageHandler.handleMsg(msg)
        if not ret:
            break

    return messageHandler


async def subscribeClient(url, credentials, channel,
                          fsqlFilter, messageHandlerClass,
                          messageHandlerArgs):
    subscribeHandlerPartial = functools.partial(
        subscribeHandler, channel=channel,
        fsqlFilter=fsqlFilter, messageHandlerClass=messageHandlerClass,
        messageHandlerArgs=messageHandlerArgs)

    ret = await client(url, credentials, subscribeHandlerPartial)
    return ret

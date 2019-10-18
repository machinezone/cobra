'''Small class to record data attached to a connection

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import rapidjson as json
import logging
import os
import tempfile
import uuid

import websockets


class ConnectionState:
    def __init__(self, appkey, userAgent):
        self.appkey = appkey
        self.userAgent = userAgent

        self.connection_id = uuid.uuid4().hex[:12]
        self.subscriptions = {}
        self.ok = True
        self.role = 'na'
        self.authenticated = False
        self.permissions = []

        self.nonce = None
        self.error = 'na'

        tempdir = tempfile.gettempdir()
        self.path = os.path.join(tempdir, f'log_{self.connection_id}')
        self.fileLogging = False

    def log(self, msg):
        log = f"[{self.connection_id}::{self.role}] {msg}"
        logging.info(log)

        if self.fileLogging:
            with open(self.path, 'a') as f:
                f.write(log + '\n')

    async def respond(self, ws, data):
        response = json.dumps(data)
        self.log(f"> {response}")

        try:
            await ws.send(response)
        except websockets.exceptions.ConnectionClosed as e:
            action = data.get('action')
            logging.warning(
                f'Trying to write action {action} in a closed connection: {e}'
            )

    def __repr__(self):
        return f"[{self.connection_id}::{self.role}::{self.userAgent}]"

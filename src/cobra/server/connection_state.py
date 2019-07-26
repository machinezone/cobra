'''Small class to record data attached to a connection

FIXME: use this to enforce publish+subscribe permissions.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import uuid


class ConnectionState:
    def __init__(self, appkey):
        self.appkey = appkey

        self.connection_id = uuid.uuid4().hex[:8]
        self.subscriptions = {}
        self.ok = True
        self.role = 'na'
        self.authenticated = False

        self.nonce = None
        self.error = 'na'

        self.path = f'/tmp/log_{self.connection_id}'
        self.fileLogging = False

    def log(self, msg):
        log = f"[{self.connection_id}::{self.role}] {msg}"
        print(log)

        if self.fileLogging:
            with open(self.path, 'a') as f:
                f.write(log + '\n')

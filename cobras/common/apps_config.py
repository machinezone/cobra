'''App configuration, persisted in a yaml file. Credentials + some config

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import base64
import binascii
import gzip
import io
import logging
import os
import tempfile
from pathlib import Path
from random import getrandbits, randint
from typing import List

import yaml

STATS_APPKEY = '_stats'
HEALTH_APPKEY = '_health'
ADMIN_APPKEY = '_admin'
PUBSUB_APPKEY = '_pubsub'


class AppsConfig:
    def __init__(self, path: str) -> None:
        self.path = path
        self.data = {}
        self.apps = {}

        if os.path.exists(self.path):
            with open(self.path) as f:
                self.data = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
                self.apps = self.data.get('apps')

            self.validateConfig()
        else:
            msg = f'Apps config file does not exists: "{path}". '
            msg += 'Use `cobra init` to create a default config file'
            logging.warning(msg)

    def validateConfig(self):
        if self.apps is None:
            raise ValueError(f'No apps present in config file')

        for app in self.apps:
            for roleName, role in self.apps[app]['roles'].items():
                if not isinstance(role, dict):
                    raise ValueError(f'role "{roleName}" is not a dict')

                if role.get('secret') is None:
                    raise ValueError(f'role "{roleName}" is missing a secret')

    def isAppKeyValid(self, appkey: str) -> bool:
        return self.apps.get(appkey) is not None

    def getRoleSecret(self, appkey: str, role: str) -> bytes:
        if not self.isAppKeyValid(appkey):
            logging.warning(f'Missing appkey: "{appkey}"')
            raise KeyError

        roles = self.apps.get(appkey, {}).get('roles')
        if roles is None:
            logging.warning(f'Missing roles')
            raise KeyError

        secret = roles.get(role, {}).get('secret')
        if secret is None:
            logging.warning(f'Missing role: "{role}"')
            raise KeyError

        return secret.encode('ascii')

    def getPermissions(self, appkey: str, role: str) -> List[str]:
        if not self.isAppKeyValid(appkey):
            logging.warning(f'Missing appkey: "{appkey}"')
            raise KeyError

        roles = self.apps.get(appkey, {}).get('roles')
        if roles is None:
            logging.warning(f'Missing roles')
            raise KeyError

        permissions = roles.get(role, {}).get('permissions', [])
        return permissions

    def isBatchPublishEnabled(self, appkey: str) -> bytes:
        if not self.isAppKeyValid(appkey):
            logging.warning(f'Missing appkey: "{appkey}"')
            raise KeyError

        batchPublish = self.apps.get(appkey, {}).get('batch_publish', False)
        return batchPublish

    def getBatchPublishSize(self):
        return self.data.get('batch_publish_size', -1)

    def getChannelMaxLength(self):
        return self.data.get('channel_max_length', 1000)

    def generateDefaultConfig(self):
        self.data['apps'] = {}

        for app in [STATS_APPKEY, HEALTH_APPKEY, ADMIN_APPKEY, PUBSUB_APPKEY]:

            # Create an app with a user/role
            self.data['apps'][app] = {}
            self.data['apps'][app]['roles'] = {}

            role = app[1:]  # remove the leading _

            self.data['apps'][app]['roles'][role] = {
                'secret': genSecret(),
                'permissions': [
                    'subscribe',
                    'unsubscribe',
                    'publish',
                    'admin',
                    'read',
                    'write',
                    'delete',
                ],
            }

        # write to disk
        with open(self.path, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)

        # dump to the console (we could pretty-print)
        with open(self.path) as f:
            print(f.read())

    def getDefaultRoleForApp(self, app) -> str:
        try:
            roles = self.data['apps'][f'_{app}'].get('roles', {})
        except KeyError:
            return ''

        try:
            roleName = list(roles.keys())[0]
        except IndexError:
            return ''

        return roleName

    def getDefaultSecretForApp(self, app) -> str:
        try:
            roles = self.data['apps'][f'_{app}'].get('roles', {})
        except KeyError:
            return ''

        try:
            roleName = list(roles.keys())[0]
        except IndexError:
            return ''

        role = roles.get(roleName, {})
        return role.get('secret', '')

    def getChannelBuilderRules(self, app) -> list:
        try:
            rules = self.data['apps'][app].get('channel_builder', {})
            return rules
        except KeyError:
            return []


def generateAppsConfig(apps_config_path_content) -> str:
    tempPath = tempfile.mktemp(suffix='_apps.yaml')
    try:
        content = base64.b64decode(apps_config_path_content)
    except binascii.Error:
        return ''

    with open(tempPath, 'wb') as f:
        try:
            decompressed = gzip.GzipFile(fileobj=io.BytesIO(content)).read()
        except OSError:
            return ''

        f.write(decompressed)

    return tempPath


def getDefaultAppsConfigPath():
    content = os.getenv('COBRA_APPS_CONFIG_CONTENT')

    if content:
        apps_config_path = generateAppsConfig(content)
        os.environ['COBRA_APPS_CONFIG'] = apps_config_path
        return apps_config_path

    path = Path.home() / '.cobra.yaml'
    return str(path)


def getDefaultPort():
    return os.getenv('COBRA_PORT', 8765)


def getDefaultEndpoint():
    return f'ws://127.0.0.1:{getDefaultPort()}'


def makeUrl(endpoint, appkey):
    return f'{endpoint}/v2?appkey={appkey}'


def generateNonce():
    bits = getrandbits(64)
    return base64.b64encode(bytearray(str(bits), 'utf8')).decode('ascii')


def genSecret():
    lowerChars = 'abcdef'
    upperChars = 'ABCDEF'
    nums = '0123456789'

    chars = lowerChars + upperChars + nums
    N = len(chars)

    secret = ''
    for _ in range(32):
        c = randint(0, N - 1)
        secret += chars[c]

    return secret

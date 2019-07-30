'''Handle credential files

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os

from cobras.common.apps_config import AppsConfig, getDefaultAppsConfigPath


def createCredentials(role, secret):
    return {'role': role, 'secret': secret}


def getDefaultRoleForApp(app) -> str:
    path = os.getenv('COBRA_APPS_CONFIG', getDefaultAppsConfigPath())
    appsConfig = AppsConfig(path)
    return appsConfig.getDefaultRoleForApp(app)


def getDefaultSecretForApp(app) -> str:
    path = os.getenv('COBRA_APPS_CONFIG', getDefaultAppsConfigPath())
    appsConfig = AppsConfig(path)
    return appsConfig.getDefaultSecretForApp(app)

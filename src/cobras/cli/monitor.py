'''Monitor cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
import uvloop

from cobras.client.credentials import (createCredentials, getDefaultRoleForApp,
                                      getDefaultSecretForApp)
from cobras.client.monitor import runMonitor
from cobras.common.apps_config import STATS_APPKEY
from cobras.common.superuser import preventRootUsage

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={STATS_APPKEY}'


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--role', default=getDefaultRoleForApp('stats'))
@click.option('--secret', default=getDefaultSecretForApp('stats'))
@click.option('--raw', is_flag=True)
@click.option('--tidy', is_flag=True)
@click.option('--subscribers', is_flag=True)
@click.option('--role_filter')
def monitor(url, role, secret, raw, role_filter, tidy, subscribers):
    '''Monitor cobra
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(role, secret)
    displayNodes = not tidy
    runMonitor(url, credentials, raw, role_filter, displayNodes, subscribers)

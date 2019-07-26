'''Monitor cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
import uvloop

from cobra.client.credentials import createCredentials
from cobra.client.monitor import runMonitor
from cobra.common.apps_config import STATS_APPKEY
from cobra.runner.superuser import preventRootUsage

DEFAULT_URL = f'ws://127.0.0.1:8765/v2?appkey={STATS_APPKEY}'


@click.command()
@click.option('--url', default=DEFAULT_URL)
@click.option('--raw', is_flag=True)
@click.option('--tidy', is_flag=True)
@click.option('--subscribers', is_flag=True)
@click.option('--role_filter')
@click.pass_obj
def monitor(auth, url, raw, role_filter, tidy, subscribers):
    '''Monitor cobra
    '''

    preventRootUsage()
    uvloop.install()

    credentials = createCredentials(auth.role, auth.secret)
    displayNodes = not tidy
    runMonitor(url, credentials, raw, role_filter, displayNodes, subscribers)

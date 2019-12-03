'''Monitor cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
from cobras.client.credentials import (
    createCredentials,
    getDefaultRoleForApp,
    getDefaultSecretForApp,
)
from cobras.client.monitor import runMonitor
from cobras.common.apps_config import STATS_APPKEY, getDefaultEndpoint, makeUrl


@click.command()
@click.option('--endpoint', default=getDefaultEndpoint())
@click.option('--appkey', default=STATS_APPKEY)
@click.option('--role', default=getDefaultRoleForApp('stats'))
@click.option('--secret', default=getDefaultSecretForApp('stats'))
@click.option('--raw', is_flag=True)
@click.option('--hide_nodes', is_flag=True)
@click.option('--hide_roles', is_flag=True)
@click.option('--hide_channels', is_flag=True)
@click.option('--subscribers', is_flag=True)
@click.option('--role_filter')
@click.option('--channel_filter')
@click.option('--system', is_flag=True)
@click.option('--once', is_flag=True)
def monitor(
    endpoint,
    appkey,
    role,
    secret,
    raw,
    role_filter,
    channel_filter,
    hide_nodes,
    hide_roles,
    hide_channels,
    subscribers,
    system,
    once,
):
    '''Monitor cobra
    '''

    url = makeUrl(endpoint, appkey)
    credentials = createCredentials(role, secret)

    runMonitor(
        url,
        credentials,
        raw,
        role_filter,
        channel_filter,
        not hide_nodes,
        not hide_roles,
        not hide_channels,
        subscribers,
        system,
        once,
    )

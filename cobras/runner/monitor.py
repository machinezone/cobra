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
@click.option('--rolename', default=getDefaultRoleForApp('stats'))
@click.option('--rolesecret', default=getDefaultSecretForApp('stats'))
@click.option('--raw', is_flag=True)
@click.option('--hide_nodes', is_flag=True)
@click.option('--hide_roles', is_flag=True)
@click.option('--hide_channels', is_flag=True)
@click.option('--subscribers', is_flag=True)
@click.option('--role_filter')
@click.option('--channel_filter')
@click.option('--system', is_flag=True)
@click.option('--once', is_flag=True)
@click.option('--tidy', is_flag=True)
def monitor(
    endpoint,
    appkey,
    rolename,
    rolesecret,
    raw,
    role_filter,
    channel_filter,
    hide_nodes,
    hide_roles,
    hide_channels,
    subscribers,
    system,
    once,
    tidy,
):
    '''Monitor cobra
    '''

    url = makeUrl(endpoint, appkey)
    credentials = createCredentials(rolename, rolesecret)

    if tidy:
        hide_nodes = True
        hide_roles = True
        hide_channels = True

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

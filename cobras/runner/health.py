'''Health check.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

Subscribe to a channel, publish and make sure a message is received
'''
import sys
import urllib.request

import click
from cobras.client.credentials import getDefaultRoleForApp, getDefaultSecretForApp
from cobras.client.health_check import (
    getDefaultHealthCheckChannel,
    getDefaultHealthCheckHttpUrl,
    healthCheck,
)
from cobras.common.apps_config import HEALTH_APPKEY, getDefaultEndpoint, makeUrl


@click.command()
@click.option('--endpoint', default=getDefaultEndpoint())
@click.option('--appkey', default=HEALTH_APPKEY)
@click.option('--http_url', default=getDefaultHealthCheckHttpUrl)
@click.option('--http', is_flag=True)
@click.option('--http_extra_check', is_flag=True)
@click.option('--rolename', default=getDefaultRoleForApp('health'))
@click.option('--rolesecret', default=getDefaultSecretForApp('health'))
@click.option('--channel', default=getDefaultHealthCheckChannel())
@click.option('--retry', is_flag=True)
def health(
    endpoint,
    appkey,
    http_url,
    http,
    http_extra_check,
    rolename,
    rolesecret,
    channel,
    retry,
):
    '''Health check

    \b
    cobra health --http
    \b
    cobra health --http --http_url 'http://127.0.0.1:8765/health/'
    \b
    '''
    url = makeUrl(endpoint, appkey)

    if http:
        print('url:', http_url)
        with urllib.request.urlopen(http_url) as response:
            html = response.read()
            print(html.decode('utf8'), end='')
    else:
        try:
            healthCheck(url, rolename, rolesecret, channel, retry, http_extra_check)
        except Exception as e:
            click.secho(f'System is unhealthy !!: {e}', fg='red')
            sys.exit(1)

    click.secho('System is healthy', fg='green')

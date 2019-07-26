'''Health check.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

Subscribe to a channel, publish and make sure a message is received
'''
import urllib.request

import click
import uvloop

from cobra.client.health_check import (getDefaultHealthCheckChannel,
                                       getDefaultHealthCheckHttpUrl,
                                       getDefaultHealthCheckUrl, healthCheck)
from cobra.runner.superuser import preventRootUsage


@click.command()
@click.option('--url', default=getDefaultHealthCheckUrl())
@click.option('--http_url', default=getDefaultHealthCheckHttpUrl)
@click.option('--http', is_flag=True)
@click.option('--channel', default=getDefaultHealthCheckChannel())
@click.pass_obj
def health(auth, url, http_url, http, channel):
    '''Health check

    \b
    cobra health --http
    \b
    cobra health --http --http_url 'http://127.0.0.1:8765/health/'
    \b
    '''
    preventRootUsage()
    uvloop.install()

    if http:
        print('url:', http_url)
        with urllib.request.urlopen(http_url) as response:
            html = response.read()
            print(html.decode('utf8'), end='')
    else:
        healthCheck(url, auth.role, auth.secret, channel)

    print('System is healthy')

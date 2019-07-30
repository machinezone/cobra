'''Run the cobra frontend

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os

import click
import sentry_sdk
import uvloop

from cobras.common.apps_config import getDefaultAppsConfigPath
from cobras.common.superuser import preventRootUsage
from cobras.server.app import AppRunner


@click.command()
@click.option('--host', envvar='COBRA_HOST', default='127.0.0.1',
              help='Binding host address. Set to 0.0.0.0 in prod environments')
@click.option('--port', envvar='COBRA_PORT', default='8765')
@click.option('--redis_urls', envvar='COBRA_REDIS_URLS',
              default='redis://localhost;redis://localhost')
@click.option('--redis_password', envvar='COBRA_REDIS_PASSWORD')
@click.option('--apps_config_path', envvar='COBRA_APPS_CONFIG',
              default=getDefaultAppsConfigPath())
@click.option('--verbose', envvar='COBRA_VERBOSE', is_flag=True)
@click.option('--prod', envvar='COBRA_PROD', is_flag=True)
@click.option('--plugins', envvar='COBRA_PLUGINS')
@click.option('--debug_memory', envvar='COBRA_DEBUG_MEMORY', is_flag=True)
@click.option('--sentry', envvar='COBRA_SENTRY', is_flag=True)
@click.option('--sentry_url', envvar='COBRA_SENTRY_URL')
@click.option('--no_stats', envvar='COBRA_NO_STATS', is_flag=True)
@click.option('--max_subscriptions', envvar='COBRA_MAX_SUSBSCRIPTIONS',
              default=-1)
@click.option('--idle_timeout', envvar='COBRA_IDLE_TIMEOUT',
              default=5 * 60,
              help='idle connections kicked out after X seconds')
def run(host, port, redis_urls, redis_password,
        apps_config_path, verbose, debug_memory, plugins,
        sentry, sentry_url, prod, no_stats, max_subscriptions, idle_timeout):
    '''Run the cobra server

    \b
    cobra run --redis_urls 'redis://localhost:7001;redis://localhost:7002'
    \b
    env COBRA_REDIS_PASSWORD=foobared cobra run
    '''
    if prod:
        os.environ['COBRA_PROD'] = '1'

    preventRootUsage()
    uvloop.install()

    if sentry and sentry_url:
        sentry_sdk.init(sentry_url)

    print('runServer', locals())
    runner = AppRunner(host, port, redis_urls,
                       redis_password, apps_config_path,
                       verbose, debug_memory, plugins,
                       not no_stats, max_subscriptions, idle_timeout)
    runner.run()

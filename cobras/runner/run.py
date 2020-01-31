'''Run the cobra frontend

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import logging
import os
import signal
import sys

import click
import sentry_sdk
from cobras.common.apps_config import generateAppsConfig, getDefaultAppsConfigPath
from cobras.common.version import getVersion
from cobras.server.app import AppRunner


@click.command()
@click.option(
    '--host',
    envvar='COBRA_HOST',
    default='127.0.0.1',
    help='Binding host address. Set to 0.0.0.0 in prod environments',
)
@click.option('--port', envvar='COBRA_PORT', default='8765')
@click.option('--redis_urls', envvar='COBRA_REDIS_URLS', default='redis://localhost')
@click.option('--redis_password', envvar='COBRA_REDIS_PASSWORD')
@click.option(
    '--apps_config_path', envvar='COBRA_APPS_CONFIG', default=getDefaultAppsConfigPath()
)
@click.option('--apps_config_path_content', envvar='COBRA_APPS_CONFIG_CONTENT')
@click.option('--prod', envvar='COBRA_PROD', is_flag=True)
@click.option('--plugins', envvar='COBRA_PLUGINS')
@click.option('--debug_memory', envvar='COBRA_DEBUG_MEMORY', is_flag=True)
@click.option(
    '--debug_memory_no_tracemalloc',
    envvar='COBRA_DEBUG_MEMORY_NO_TRACEMALLOC',
    is_flag=True,
)
@click.option(
    '--debug_memory_print_all_tasks',
    envvar='COBRA_DEBUG_MEMORY_PRINT_ALL_TASKS',
    is_flag=True,
)
@click.option('--sentry', envvar='COBRA_SENTRY', is_flag=True)
@click.option('--sentry_url', envvar='COBRA_SENTRY_URL')
@click.option('--no_stats', envvar='COBRA_NO_STATS', is_flag=True)
@click.option('--max_subscriptions', envvar='COBRA_MAX_SUSBSCRIPTIONS', default=-1)
@click.option(
    '--idle_timeout',
    envvar='COBRA_IDLE_TIMEOUT',
    default=5 * 60,
    help='idle connections kicked out after X seconds',
)
@click.option(
    '--disable_redis_startup_probing',
    envvar='COBRA_DISABLE_REDIS_STARTUP_PROBING',
    is_flag=True,
)
@click.option(
    '--redis_startup_probing_timeout',
    envvar='COBRA_REDIS_STARTUP_PROBING_TIMEOUT',
    default=30,
)
@click.option('--environment', envvar='COBRA_ENVIRONMENT', default='dev')
def run(
    host,
    port,
    redis_urls,
    redis_password,
    apps_config_path,
    apps_config_path_content,
    debug_memory,
    debug_memory_no_tracemalloc,
    debug_memory_print_all_tasks,
    plugins,
    sentry,
    sentry_url,
    prod,
    no_stats,
    max_subscriptions,
    idle_timeout,
    disable_redis_startup_probing,
    redis_startup_probing_timeout,
    environment,
):
    '''Run the cobra server

    \b
    cobra run --redis_urls 'redis://localhost:7001;redis://localhost:7002'
    \b
    env COBRA_REDIS_PASSWORD=foobared cobra run
    '''
    if prod:
        os.environ['COBRA_PROD'] = '1'

    if sentry and sentry_url:
        sentry_sdk.init(
            sentry_url,
            release=getVersion(),
            environment=environment,
            attach_stacktrace=True,
        )

    if apps_config_path_content:
        apps_config_path = generateAppsConfig(apps_config_path_content)
        if not apps_config_path:
            logging.error(
                f'Invalid apps config path content: {apps_config_path_content}'
            )
            logging.error(f'(usually configured with $COBRA_APPS_CONFIG_CONTENT)')
            logging.error(f'Generate it with `gzip -c ~/.cobra.yaml | base64`')
            sys.exit(1)

        apps_config_path_content = '<cleared>'
        os.environ['COBRA_APPS_CONFIG'] = apps_config_path

    print('runServer', locals())
    runner = AppRunner(
        host,
        port,
        redis_urls,
        redis_password,
        apps_config_path,
        debug_memory,
        debug_memory_no_tracemalloc,
        debug_memory_print_all_tasks,
        plugins,
        not no_stats,
        max_subscriptions,
        idle_timeout,
        probeRedisOnStartup=not disable_redis_startup_probing,
        redisStartupProbingTimeout=redis_startup_probing_timeout,
    )

    loop = asyncio.get_event_loop()
    stop = loop.create_future()

    asyncio.get_event_loop().add_signal_handler(signal.SIGTERM, stop.set_result, None)

    try:
        runner.run(stop)
    except Exception as e:
        logging.fatal(f'Cannot start cobra server: {e}')
        sys.exit(1)

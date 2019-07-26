'''Cobra main driver.
   Calls into sub commands like git.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
import coloredlogs

from cobra.common.version import getVersion
from cobra.runner.commands.admin import admin
from cobra.runner.commands.health import health
from cobra.runner.commands.init import init
from cobra.runner.commands.monitor import monitor
from cobra.runner.commands.publish import publish
from cobra.runner.commands.redis_subscribe import redis_subscribe
from cobra.runner.commands.run import run
from cobra.runner.commands.secret import secret
from cobra.runner.commands.subscribe import subscribe

coloredlogs.install(level='WARNING')


@click.group()
@click.version_option(version=getVersion())
def cli():
    '''Cobra is a realtime messaging server using
    Python3, WebSockets and Redis.'''
    pass


cli.add_command(run)
cli.add_command(publish)
cli.add_command(subscribe)
cli.add_command(redis_subscribe)
cli.add_command(monitor)
cli.add_command(health)
cli.add_command(secret)
cli.add_command(admin)
cli.add_command(init)

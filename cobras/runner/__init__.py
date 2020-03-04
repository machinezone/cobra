'''Cobra main driver.
   Calls into sub commands like git.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

# flake8: noqa
'''

from pkgutil import walk_packages

import click
import coloredlogs
import uvloop

from cobras.common.atexit_profiler import registerProfiler

from cobras.common.atexit_profiler import registerProfiler

LOGGING_FORMAT = '%(asctime)s %(levelname)s %(message)s'
coloredlogs.install(level='WARNING', fmt=LOGGING_FORMAT)


@click.option('--verbose', '-v', envvar='COBRA_VERBOSE', is_flag=True)
@click.option('--profile', envvar='COBRA_PROFILE', is_flag=True)
@click.option('--uv', '-u', envvar='COBRA_UVLOOP', is_flag=True, help='Use uvloop')
@click.group()
@click.version_option()
def main(verbose, profile, uv):
>>>>>>> add ability to select redis library used
    """\b
   ___      _
  / __\___ | |__  _ __ __ _
 / /  / _ \| '_ \| '__/ _` |
/ /__| (_) | |_) | | | (_| |
\____/\___/|_.__/|_|  \__,_|

Cobra is a realtime messaging server using Python3, WebSockets and Redis.
    """
    if uv:
        uvloop.install()

    if verbose:
        level = 'INFO' if verbose == 1 else 'DEBUG'
        coloredlogs.install(level='INFO', fmt=LOGGING_FORMAT)

    if profile:
        registerProfiler()


for loader, module_name, is_pkg in walk_packages(__path__, __name__ + '.'):
    module = __import__(module_name, globals(), locals(), ['__name__'])
    cmd = getattr(module, module_name.rsplit('.', 1)[-1])
    if isinstance(cmd, click.Command):
        main.add_command(cmd)

'''Bavarde main driver.
   Calls into sub commands like git.

Copyright (c) 2019 Machine Zone, Inc. All rights reserved.
'''

from pkgutil import walk_packages

import click
import coloredlogs

coloredlogs.install(level='WARNING')


@click.group()
@click.version_option()
def main():
    """\b

Bavarde is a chat app written on top of cobra
"""


for loader, module_name, is_pkg in walk_packages(__path__, __name__ + '.'):
    module = __import__(module_name, globals(), locals(), ['__name__'])
    cmd = getattr(module, module_name.rsplit('.', 1)[-1])
    if isinstance(cmd, click.Command):
        main.add_command(cmd)

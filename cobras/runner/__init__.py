'''Cobra main driver.
   Calls into sub commands like git.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click
import coloredlogs

from pkgutil import walk_packages

coloredlogs.install(level='WARNING')

@click.group()
@click.version_option()
def main():
    """\b
   ___      _
  / __\___ | |__  _ __ __ _
 / /  / _ \| '_ \| '__/ _` |
/ /__| (_) | |_) | | | (_| |
\____/\___/|_.__/|_|  \__,_|
		
Cobra is a realtime messaging server using Python3, WebSockets and Redis.
"""


for loader, module_name, is_pkg in walk_packages(__path__, __name__ + '.'):
    module = __import__(module_name, globals(), locals(), ['__name__'])
    cmd = getattr(module, module_name.rsplit('.', 1)[-1])
    if isinstance(cmd, click.Command):
        main.add_command(cmd)

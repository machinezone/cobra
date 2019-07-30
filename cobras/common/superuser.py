'''Tools used when running as superuser (which we should almost never do)

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os
import sys

import click


def preventRootUsage():
    ''' Make sure a root user cannot run this command'''

    if os.geteuid() == 0:
        msg = 'Cobra cannot be run as root / sudo. Exiting'
        click.secho(msg, fg='red')
        sys.exit(1)

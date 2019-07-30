'''Generate secrets used for authentication

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import click

from cobras.common.apps_config import genSecret
from cobras.common.superuser import preventRootUsage


@click.command()
def secret():
    '''
    Generate secrets used for authentication

    \b
    cobra secret
    '''

    preventRootUsage()

    secret = genSecret()
    print(secret)

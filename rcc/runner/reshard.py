'''Tools to reshard a redis cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import resource
import click

from rcc.cluster.reshard import binPackingReshard

DEFAULT_WEIGHTS_PATH = 'weights.csv'


@click.command()
@click.option('--port', default=6379)
@click.option('--redis_url', default='redis://localhost:11000')
@click.option('--weight', '-w', required=True, default=DEFAULT_WEIGHTS_PATH)
@click.option('--dry', is_flag=True)
@click.option('--node_id')
@click.option('--timeout', default=15, help='Max time to wait for consistency check')
def reshard(port, redis_url, weight, timeout, dry, node_id):
    '''Reshard using the bin-packing technique
    '''

    nofile = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    click.secho(f'file descriptors ulimit: {nofile}', fg='cyan')
    click.secho(
        f'resharding can be hungry, bump it with ulimit -n if needed', fg='cyan'
    )

    binPackingReshard(redis_url, weight, timeout, dry, node_id)

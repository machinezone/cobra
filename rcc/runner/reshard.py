'''Tools to reshard a redis cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import click

from rcc.cluster.reshard import binPackingReshard

DEFAULT_WEIGHTS_PATH = 'weights.csv'


@click.command()
@click.option('--port', default=6379)
@click.option('--redis_url', default='redis://localhost:11000')
@click.option('--weight', '-w', required=True, default=DEFAULT_WEIGHTS_PATH)
@click.option('--dry', is_flag=True)
@click.option('--node_id')
def reshard(port, redis_url, weight, dry, node_id):
    '''Reshard using the bin-packing technique
    '''

    binPackingReshard(redis_url, weight, dry, node_id)

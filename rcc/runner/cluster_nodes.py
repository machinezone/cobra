'''Repeatitly print cluster info

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import click

from rcc.cluster.info import printRedisClusterInfoCoro


@click.command()
@click.option('--redis_urls', default='redis://localhost:11000')
@click.option('--role', '-r')
def cluster_nodes(redis_urls, role):
    '''Monitor redis metrics

    \b
    rcc cluster-nodes
    '''

    asyncio.run(printRedisClusterInfoCoro(redis_urls, role))

'''Repeatitly print cluster info

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''
import asyncio
import click

from rcc.cluster.info import clusterCheck


async def checkCluster(redis_urls):
    ok = await clusterCheck(redis_urls)
    print('cluster ok:', ok)


@click.command()
@click.option('--redis_urls', default='redis://localhost:11000')
def cluster_check(redis_urls):
    '''Similar to redis-cli --cluster check

    Make sure all nodes have the same view of the cluster
    '''

    asyncio.run(checkCluster(redis_urls))

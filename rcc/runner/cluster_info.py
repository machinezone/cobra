'''Repeatitly print cluster info

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''
import asyncio

import click
import tabulate

from rcc.client import RedisClient


async def printRedisClusterInfoCoro(redisClient, stats, role=None):
    nodes = await redisClient.cluster_nodes()

    clients = []
    for node in nodes:
        if role is not None and node.role != role:
            continue

        url = f'redis://{node.ip}:{node.port}'
        client = RedisClient(url, '')
        clients.append((node, client))

    while True:
        rows = [['node', 'role', *stats]]

        for node, client in clients:
            info = await client.info()

            row = [node.ip + ':' + node.port, node.role]
            for stat in stats:
                row.append(info[stat])

            rows.append(row)

        click.clear()
        print(tabulate.tabulate(rows, tablefmt="simple", headers="firstrow"))
        await asyncio.sleep(1)


def printRedisClusterInfo(redis_urls, stats, role):
    redisClient = RedisClient(redis_urls, '')
    asyncio.run(printRedisClusterInfoCoro(redisClient, stats, role))


@click.command()
@click.option('--redis_urls', default='redis://localhost:10000')
@click.option('--stats', '-s', default=['redis_version'], multiple=True)
@click.option('--role', '-r')
def cluster_info(redis_urls, stats, role):
    '''Monitor redis metrics

    \b
    rcc cluster-info --stats instantaneous_input_kbps

    Example ones:

    * instantaneous_input_kbps
    * instantaneous_output_kbps
    * connected_clients
    * used_memory_rss_human
    '''

    printRedisClusterInfo(redis_urls, stats, role)

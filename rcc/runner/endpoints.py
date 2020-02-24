'''Tools to display endpoints associated with a redis cluster deploy

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os
import json

import click
import tabulate

from rcc.client import RedisClient


def getEndpointsIps(service):
    '''
    kubectl get endpoints -o json redis-cluster
    '''

    content = os.popen(f'kubectl get endpoints -o json {service}').read()
    data = json.loads(content)

    assert len(data['subsets']) == 1
    assert 'addresses' in data['subsets'][0]
    addresses = data['subsets'][0]['addresses']

    ips = []
    for address in addresses:
        ip = address.get('ip')
        ips.append(ip)

    return ips


def printEndpoints(service, port):
    ips = getEndpointsIps(service)

    endpoints = []
    for ip in ips:
        endpoints.append(f'redis://{ip}:{port}')

    print(';'.join(endpoints))


def printRedisClusterInitCommand(service, port):
    cmd = 'redis-cli --cluster create '

    ips = getEndpointsIps(service)

    for ip in ips:
        cmd += f'{ip}:{port} '

    cmd += ' --cluster-replicas 1'

    print(cmd)


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
@click.option('--service', default='redis-cluster')
@click.option('--port', default=6379)
def endpoints(service, port):
    '''Print endpoints associated with a redis cluster service
    '''

    printEndpoints(service, port)

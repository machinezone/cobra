'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os
import json
import click


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


@click.command()
@click.option('--action', default='get_endpoints')
@click.option('--service', default='redis-cluster')
@click.option('--port', default=6379)
def redis_cluster(action, service, port):
    '''Help with redis cluster operations

    \bcobra redis-cluster --service redis-cluster --action redis_cluster_init
    '''

    if action == 'get_endpoints':
        printEndpoints(service, port)
    elif action == 'redis_cluster_init':
        printRedisClusterInitCommand(service, port)

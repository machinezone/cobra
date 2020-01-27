'''Subscribe to a channel

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os
import json
import click


def getEndpoints(service, port):
    '''
    kubectl get endpoints -o json redis-cluster
    '''

    content = os.popen(f'kubectl get endpoints -o json {service}').read()
    data = json.loads(content)

    assert len(data['subsets']) == 1
    assert 'addresses' in data['subsets'][0]
    addresses = data['subsets'][0]['addresses']

    endpoints = []
    for address in addresses:
        ip = address.get('ip')
        endpoints.append(f'redis://{ip}:{port}')

    print(';'.join(endpoints))


@click.command()
@click.option('--action', default='get_endpoints')
@click.option('--service', default='redis-cluster')
@click.option('--port', default=6379)
def redis_cluster(action, service, port):
    '''Help with redis cluster operations
    '''

    if action == 'get_endpoints':
        getEndpoints(service, port)

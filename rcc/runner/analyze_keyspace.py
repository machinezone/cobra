'''Tool to analyze the keyspace

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import click

from rcc.cluster.keyspace_analyzer import analyzeKeyspace, writeWeightsToCsv
from rcc.plot import asciiPlot


@click.command()
@click.option('--redis_url', default='redis://localhost')
@click.option('--redis_password')
@click.option('--timeout', default=5)
@click.option('--port', default=6379)
@click.option('--path', '-w', default='weights.csv')
@click.option('--quiet', '-q', is_flag=True)
def analyze_keyspace(redis_url, port, redis_password, timeout, path, quiet):
    '''Analyze keyspace

    \b
    rcc analyze-keyspace --redis_url redis://localhost:11000 --timeout 3

    Insert keys with this command
    \b
    redis-cli -p 11000 flushdb ; rcc publish -p 11000 --batch --random_channel
    '''

    keySpace = asyncio.run(analyzeKeyspace(redis_url, timeout, progress=not quiet))
    weights = keySpace.keys
    writeWeightsToCsv(weights, path)

    # print key access by redis node
    # for node, access in sorted(result['nodes'].items()):
    #    print(node, access)

    asciiPlot('Nodes', keySpace.nodes)

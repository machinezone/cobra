'''Tool to analyze the keyspace

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import click

from rcc.cluster.keyspace_analyzer import analyzeKeyspace, writeWeightsToCsv


@click.command()
@click.option('--redis_url', default='redis://localhost')
@click.option('--redis_password')
@click.option('--timeout', default=360)
@click.option('--port', default=6379)
@click.option('--path', default='weights.csv')
def analyze_keyspace(redis_url, port, redis_password, timeout, path):
    '''Subscribe to a channel

    \b
    rcc analyze-keyspace --redis_url redis://localhost:10000 --timeout 60
    '''

    weights = asyncio.run(analyzeKeyspace(redis_url, timeout))
    writeWeightsToCsv(weights, path)

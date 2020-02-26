'''Help create a temp cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os
import sys
import time
import logging

import click

from rcc.cluster.info import clusterCheck
from rcc.client import RedisClient


def makeServerConfig(root, startPort=11000, masterNodeCount=3):

    # create config files
    for i in range(masterNodeCount * 2):

        serverPath = os.path.join(root, f'server{i}.conf')
        with open(serverPath, 'w') as f:
            # Config file contains:
            # cluster-config-file nodes-1.conf
            # dbfilename dump1.rdb
            f.write(f'cluster-config-file nodes-{i}.conf' + '\n')
            f.write(f'dbfilename dump{i}.rdb')

    # Create a Procfile
    # server1: redis-server server1.conf --protected-mode no ...
    # server2: redis-server server2.conf --protected-mode no ...
    procfile = os.path.join(root, 'Procfile')
    with open(procfile, 'w') as f:
        for i in range(masterNodeCount * 2):
            port = startPort + i
            f.write(f'server{i}: redis-server server{i}.conf ')
            f.write(f'--protected-mode no --cluster-enabled yes --port {port}\n')

    # Print cluster init command
    ips = ' '.join(
        ['127.0.0.1:' + str(startPort + i) for i in range(masterNodeCount * 2)]
    )
    host = 'localhost'
    port = startPort
    clusterInitCmd = f'echo yes | redis-cli -h {host} -p {port} '
    clusterInitCmd += f'--cluster create {ips} --cluster-replicas 1'

    return clusterInitCmd


async def runServer(root, startPort):
    try:
        proc = await asyncio.create_subprocess_shell('honcho start', cwd=root)
        stdout, stderr = await proc.communicate()
    except asyncio.CancelledError:
        print('Cancelling honcho')
        proc.terminate()


async def initCluster(cmd):
    proc = await asyncio.create_subprocess_shell(cmd)
    stdout, stderr = await proc.communicate()


async def checkOpenedPort(portRange, timeout: int):
    # start by making sure that all ports are free.
    # There is still room for data race but it's better than nothing
    start = time.time()

    for port in portRange:
        while True:
            sys.stderr.write('.')
            sys.stderr.flush()

            if time.time() - start > timeout:
                sys.stderr.write('\n')
                raise ValueError(f'Timeout trying to check opened ports {portRange}')

            # FIXME there's probably a more portable thing that using nc
            cmd = f'nc -vz -w 1 localhost {port} 2> /dev/null'
            ret = os.system(cmd)

            if ret == 0:
                # if we can connect it's not good, wait a bit, or
                # we could straight out error out
                await asyncio.sleep(0.1)
            else:
                break

    sys.stderr.write('\n')


# FIXME: cobra could use this version
async def waitForAllConnectionsToBeReady(urls, password, timeout: int):
    start = time.time()

    for url in urls:
        sys.stderr.write(f'Checking {url} ')

        while True:
            sys.stderr.write('.')
            sys.stderr.flush()

            try:
                redis = RedisClient(url, password)
                await redis.connect()
                await redis.send('PING')
                redis.close()
                break
            except Exception as e:
                if time.time() - start > timeout:
                    sys.stderr.write('\n')
                    raise

                logging.warning(e)

                waitTime = 0.1
                await asyncio.sleep(waitTime)
                timeout -= waitTime

        sys.stderr.write('\n')


async def runNewCluster(root, startPort, size):
    size = int(size)

    portRange = [port for port in range(startPort, startPort + 2 * size)]
    click.secho(f'1/6 Creating server config for range {portRange}', bold=True)

    initCmd = makeServerConfig(root, startPort, size)

    click.secho('2/6 Check that ports are opened', bold=True)
    await checkOpenedPort(portRange, timeout=10)

    try:
        click.secho(f'3/6 Configuring and running', bold=True)
        task = asyncio.create_task(runServer(root, startPort))

        # Check that all connections are ready
        click.secho(f'4/6 Wait for the cluster nodes to be running', bold=True)
        urls = [
            f'redis://localhost:{port}' for port in range(startPort, startPort + size)
        ]
        await waitForAllConnectionsToBeReady(urls, password='', timeout=5)

        # Initialize the cluster (master/slave assignments, etc...)
        click.secho(f'5/6 Initialize the cluster', bold=True)
        await initCluster(initCmd)

        # We just initialized the cluster, wait until it is 'consistent' and good to use
        click.secho(f'6/6 Wait for all cluster nodes to be consistent', bold=True)

        redisUrl = f'redis://localhost:{startPort}'
        while True:
            ret = False
            try:
                ret = await clusterCheck(redisUrl)
            except Exception:
                pass

            if ret:
                break

            print('Waiting for cluster to be consistent...')
            await asyncio.sleep(1)

        click.secho('Cluster ready !', fg='green')

        path = os.path.join(root, 'redis_cluster_ready')
        with open(path, 'w') as f:
            f.write('cluster ready')

        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        print('Cancelling cluster')

    finally:
        task.cancel()

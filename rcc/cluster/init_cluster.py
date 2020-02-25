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
    # first start by making sure that all ports are free.
    # There is still room for data race but it's better than nothing

    for port in range(startPort, startPort + 6):
        while True:
            sys.stderr.write('.')
            sys.stderr.flush()

            cmd = f'nc -vz localhost {port} 2> /dev/null'
            ret = os.system(cmd)

            if ret == 0:
                # if we can connect it's not good, wait a bit, or
                # we could straight out error out
                await asyncio.sleep(0.1)
            else:
                break

    sys.stderr.write('\n')
    print('Free ports')

    try:
        os.chdir(root)
        proc = await asyncio.create_subprocess_shell('honcho start')
        stdout, stderr = await proc.communicate()
    except asyncio.CancelledError:
        print('Cancelling honcho')
        await proc.terminate()


async def initCluster(cmd):
    proc = await asyncio.create_subprocess_shell(cmd)
    stdout, stderr = await proc.communicate()


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

    initCmd = makeServerConfig(root, startPort, size)

    try:
        task = asyncio.create_task(runServer(root, startPort))

        # Check that all connections are ready
        urls = [
            f'redis://localhost:{port}' for port in range(startPort, startPort + size)
        ]
        await waitForAllConnectionsToBeReady(urls, password='', timeout=5)

        # Initialize the cluster (master/slave assignments, etc...)
        await initCluster(initCmd)

        # We just initialized the cluster, wait until it is 'consistent' and good to use
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

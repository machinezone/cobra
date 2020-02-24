'''Help create a temp cluster

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import os


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


async def runServer(root):
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


async def runNewCluster(root, startPort, size):
    size = int(size)

    initCmd = makeServerConfig(root, startPort, size)

    try:
        task = asyncio.create_task(runServer(root))
        await asyncio.sleep(1)

        await initCluster(initCmd)

        path = os.path.join(root, 'ready')
        with open(path, 'w') as f:
            f.write('cluster ready')

        while True:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        print('Cancelling cluster')

    finally:
        task.cancel()

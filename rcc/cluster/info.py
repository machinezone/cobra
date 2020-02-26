'''Cluster info tools

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import collections
import hashlib
import logging

from rcc.client import RedisClient


async def getSlotsToNodesMapping(redis_urls):
    redisClient = RedisClient(redis_urls, '')
    nodes = await redisClient.cluster_nodes()

    masterNodes = [node for node in nodes if node.role == 'master']

    # We need to know where each slots lives
    slotToNodes = {}
    for node in masterNodes:
        for slot in node.slots:
            slotToNodes[slot] = node

    return slotToNodes


def getSlotsRange(slots):
    '''I failed the programming interview quizz but the function
       works like redis CLUSTER NODES
    '''

    if len(slots) == 0:
        return ''

    ranges = []

    equal = False
    firstSlot = slots[0]

    for i in range(1, len(slots)):

        if slots[i - 1] + 1 == slots[i]:
            # last entry
            if i == (len(slots) - 1):
                ranges.append((firstSlot, slots[i]))
            continue
        else:
            equal = False
            ranges.append((firstSlot, slots[i - 1]))
            firstSlot = slots[i]

        # last entry
        if i == (len(slots) - 1):
            if not equal:
                ranges.append((slots[i], slots[i]))
            else:
                ranges.append((firstSlot, slots[i]))

    res = []
    for r in ranges:
        if r[0] == r[1]:
            res.append(str(r[0]))
        else:
            res.append('{}-{}'.format(r[0], r[1]))

    return ' '.join(res)


async def printRedisClusterInfoCoro(redisUrl, role=None):
    redisClient = RedisClient(redisUrl, '')
    nodes = await redisClient.cluster_nodes()

    for node in nodes:
        if role is not None and node.role != role:
            continue

        slotRange = getSlotsRange(node.slots)
        print(node.node_id, node.ip + ':' + node.port, node.role, slotRange)


async def getClusterSignature(redisUrl):
    redisClient = RedisClient(redisUrl, '')
    nodes = await redisClient.cluster_nodes()

    roles = collections.defaultdict(int)
    allSlots = set()

    signature = ''
    for node in nodes:
        roles[node.role] += 1

        slotRange = getSlotsRange(node.slots)
        tokens = [node.node_id, node.ip + ':' + node.port, node.role, slotRange]
        signature += ' '.join(tokens) + '\n'

        for slot in node.slots:
            allSlots.add(slot)

    fullCoverage = len(allSlots) == 16384
    balanced = roles['master'] <= roles['slave']

    return signature, balanced, fullCoverage


async def getClusterUrls(redisUrl):
    redisClient = RedisClient(redisUrl, '')
    nodes = await redisClient.cluster_nodes()

    urls = []
    for node in nodes:
        url = f'redis://{node.ip}:{node.port}'
        urls.append(url)

    return urls


async def clusterCheck(redisUrl, verbose=False):
    '''
    Get all the nodes in the cluster
    Then ask each nodes its view of the cluster (mostly allocated slots)
    Compare each view and make sure they are consistent
    '''
    urls = await getClusterUrls(redisUrl)

    signatures = set()

    allBalanced = True
    allCovered = True

    for url in urls:
        signature, balanced, fullCoverage = await getClusterSignature(url)
        signatures.add(signature)

        allBalanced = allBalanced and balanced
        allCovered = allCovered and fullCoverage

        cksum = hashlib.md5(signature.encode('utf-8')).hexdigest()

        logging.info(f'{url} {cksum} balanced {balanced} coverage {fullCoverage}')
        logging.info('\n' + signature)

    logging.info(f'{len(signatures)} unique signatures')

    return len(signatures) == 1 and allBalanced and allCovered

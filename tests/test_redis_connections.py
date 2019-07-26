'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import asyncio

from cobra.server.redis_connections import RedisConnections


async def passwordTestCoroutine():
    redisUrls = 'redis://localhost'
    redisPassword = None
    redisConnections = RedisConnections(redisUrls, redisPassword)
    assert redisConnections.password == None

    redisPassword = ''
    redisConnections = RedisConnections(redisUrls, redisPassword)
    assert redisConnections.password == None


def test_password_default():
    asyncio.get_event_loop().run_until_complete(passwordTestCoroutine())


async def hashingDistributionCoroutine(redisUrls):
    redisPassword = None
    redisConnections = RedisConnections(redisUrls, redisPassword)

    urls = []

    for i in range(16):
        for game in ['ody', 'wiso', 'niso', 'miso', 'gof']:
            shard = f'sms_live_shard_v1.{game}.{i}'
            url = redisConnections.hashChannel(shard)
            urls.append((url, shard))

    urls.sort()
    for i, url in enumerate(urls):
        print(i, url)


def test_hashing_distribution():
    redisUrls = 'redis://A;redis://B'
    asyncio.get_event_loop().run_until_complete(hashingDistributionCoroutine(redisUrls))

    redisUrls = 'redis://A;redis://B;redis://C'
    asyncio.get_event_loop().run_until_complete(hashingDistributionCoroutine(redisUrls))


async def hashingConsistencyTestCoroutine(redisUrls):
    redisPassword = None
    redisConnections = RedisConnections(redisUrls, redisPassword)

    game = 'ody'
    i = 0
    shard = f'sms_live_shard_v1.{game}.{i}'
    url = redisConnections.hashChannel(shard)
    assert url == 'redis://A'

    game = 'ody'
    i = 12
    shard = f'sms_live_shard_v1.{game}.{i}'
    url = redisConnections.hashChannel(shard)
    assert url == 'redis://A'

    game = 'niso'
    i = 15
    shard = f'sms_live_shard_v1.{game}.{i}'
    url = redisConnections.hashChannel(shard)
    assert url == 'redis://C'

    game = 'miso'
    i = 15
    shard = f'sms_live_shard_v1.{game}.{i}'
    url = redisConnections.hashChannel(shard)
    assert url == 'redis://C'

    game = 'gof'
    i = 6
    shard = f'sms_live_shard_v1.{game}.{i}'
    url = redisConnections.hashChannel(shard)
    assert url == 'redis://A'


def test_validate_hashing_consistency():
    redisUrls = 'redis://A;redis://B;redis://C'
    asyncio.get_event_loop().run_until_complete(hashingConsistencyTestCoroutine(redisUrls))

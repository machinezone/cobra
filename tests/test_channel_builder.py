'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import os
import random

from cobras.common.apps_config import AppsConfig
from cobras.common.channel_builder import updateMsg


def test_compose2():
    random.seed(0)
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder.yaml')

    appsConfig = AppsConfig(path)
    appkey = 'health'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {
        'action': 'rtm/publish',
        'body': {
            'message': {'device': {'game': 'ody'}, 'id': 'engine_fps_id'},
            'channels': ['sms_republished_v1_neo'],
        },
    }

    updatedMsg = updateMsg(rules, msg)

    channels = updatedMsg['body']['channels']
    assert len(channels) == 5

    assert 'sms_republished_v1_neo' in channels
    assert 'ody_engine_fps_id' in channels
    assert 'foo' in channels
    assert 'bar' in channels
    assert 'subscriber_republished_3' in channels


def test_some_empty_fields():
    random.seed(0)

    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder.yaml')

    appsConfig = AppsConfig(path)
    appkey = 'health'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {
        'action': 'rtm/publish',
        'body': {
            'message': {
                'data': {
                    'rate_control': {
                        'engine_fps_id': 60,
                        'engine_memory_used_id': 60,
                        'engine_message_loop_id': 86400,
                    }
                },
                'device': None,
                'id': 'sms_set_rate_control_id',
                'per_id_counter': 0,
                'session': '98c3eb2c042e42068fc4d2b39fe720f8',
                'timestamp': 1582066343026,
                'version': 1,
            },
            'channels': ['a_channel'],
        },
    }

    updatedMsg = updateMsg(rules, msg)

    channels = updatedMsg['body']['channels']
    assert len(channels) == 4

    assert 'a_channel' in channels
    assert 'foo' in channels
    assert 'bar' in channels
    assert 'subscriber_republished_3' in channels


def test_remove_channel():
    random.seed(10)
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder.yaml')

    appsConfig = AppsConfig(path)
    appkey = 'health'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {
        'action': 'rtm/publish',
        'body': {
            'message': {
                'data': {
                    'rate_control': {
                        'engine_fps_id': 60,
                        'engine_memory_used_id': 60,
                        'engine_message_loop_id': 86400,
                    }
                },
                'device': None,
                'id': 'sms_set_rate_control_id',
                'per_id_counter': 0,
                'session': '98c3eb2c042e42068fc4d2b39fe720f8',
                'timestamp': 1582066343026,
                'version': 1,
            },
            'channels': ['a_channel', 'sms_live_shard_v1.wiso.9'],
        },
    }

    updatedMsg = updateMsg(rules, msg)

    channels = updatedMsg['body']['channels']
    assert len(channels) == 4

    assert 'a_channel' in channels
    assert 'sms_live_shard_v1.wiso.9' not in channels
    assert 'bar' in channels
    assert 'subscriber_republished_0' in channels


def test_add_shard():
    random.seed(10)

    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder.yaml')

    appsConfig = AppsConfig(path)
    appkey = 'health'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {
        'action': 'rtm/publish',
        'body': {
            'message': {
                'data': {
                    'rate_control': {
                        'engine_fps_id': 60,
                        'engine_memory_used_id': 60,
                        'engine_message_loop_id': 86400,
                    }
                },
                'device': None,
                'id': 'sms_set_rate_control_id',
                'per_id_counter': 0,
                'session': '98c3eb2c042e42068fc4d2b39fe720f8',
                'timestamp': 1582066343026,
                'version': 1,
            },
            'channels': ['a_channel', 'sms_live_shard_v1.wiso.9'],
        },
    }

    channels = set()
    for i in range(1, 1000):
        updatedMsg = updateMsg(rules, msg)
        channels.update(updatedMsg['body']['channels'])

    assert 'a_channel' in channels
    assert 'sms_live_shard_v1.wiso.9' not in channels
    assert 'bar' in channels
    assert 'subscriber_republished_0' in channels
    assert 'subscriber_republished_1' in channels
    assert 'subscriber_republished_2' in channels
    assert 'subscriber_republished_3' in channels


def test_no_rules():
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder_no_rules.yaml')

    appsConfig = AppsConfig(path)
    appkey = '_pubsub'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {'action': 'rtm/publish', 'body': {'channels': ['a_channel']}}

    updatedMsg = updateMsg(rules, msg)

    channels = updatedMsg['body']['channels']
    assert len(channels) == 1

    assert 'a_channel' in channels


def test_none_error():
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps_channel_builder_none_error.yaml')

    appsConfig = AppsConfig(path)
    appkey = '_pubsub'
    rules = appsConfig.getChannelBuilderRules(appkey)

    msg = {'action': 'rtm/publish', 'body': {'channels': ['a_channel']}}

    updatedMsg = updateMsg(rules, msg)

    channels = updatedMsg['body']['channels']
    assert len(channels) == 1

    assert 'a_channel' in channels

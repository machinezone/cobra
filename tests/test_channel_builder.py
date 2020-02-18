'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import os

from cobras.common.apps_config import AppsConfig
from cobras.common.channel_builder import updateMsg


def test_compose2():
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
    assert len(channels) == 3

    assert 'sms_republished_v1_neo' in channels
    assert 'ody_engine_fps_id' in channels
    assert 'foo' in channels

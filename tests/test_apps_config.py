'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import os

import pytest

from cobras.common.apps_config import AppsConfig


def test_answer():
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps.yaml')

    appsConfig = AppsConfig(path)
    assert not appsConfig.isAppKeyValid('ASDCSDC')
    assert appsConfig.isAppKeyValid('AAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB')
    assert appsConfig.isAppKeyValid('eeeeeeeeeeeeeeeeffffffffffffffff')
    assert appsConfig.isAppKeyValid('aaaaaaaaaaaaaaaabbbbbbbbbbbbbbbb')
    assert appsConfig.isAppKeyValid('_health')

    with pytest.raises(KeyError):
        appsConfig.getRoleSecret('blah', 'blah')

    with pytest.raises(KeyError):
        appsConfig.getRoleSecret('C1bD8A3F2Da58C43F0CBB357fe9c5b9a', 'blah')

    secret = appsConfig.getRoleSecret('eeeeeeeeeeeeeeeeffffffffffffffff',
                                      'client_publisher')
    assert secret == b'ggggggggggggggggggghhhhhhhhhhhhH'

    batchPublish = appsConfig.isBatchPublishEnabled('AAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB')
    assert not batchPublish

    batchPublish = appsConfig.isBatchPublishEnabled('eeeeeeeeeeeeeeeeffffffffffffffff')
    assert batchPublish


def test_get_roles_and_secret():
    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, 'test_data', 'apps_config')
    path = os.path.join(dataDir, 'apps.yaml')

    appsConfig = AppsConfig(path)

    role = appsConfig.getDefaultRoleForApp('app_that_does_not_exist')
    assert role == ''

    secret = appsConfig.getDefaultSecretForApp('app_that_does_not_exist')
    assert secret == ''

    role = appsConfig.getDefaultRoleForApp('health')
    assert role == 'health'

    secret = appsConfig.getDefaultSecretForApp('health')
    assert secret == 'e3Ae82633cd59b22daea958bbb82ac92'


def test_empty_apps_file():
    appsConfig = AppsConfig('')
    assert not appsConfig.isAppKeyValid('ASDCSDC')

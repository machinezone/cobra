'''Compute our version number

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os

from cobras.common.memoize import memoize


@memoize
def getVersion():
    '''Get our own version using pkg_resources'''

    root = os.path.dirname(os.path.realpath(__file__))
    dataDir = os.path.join(root, '..', '..')
    path = os.path.join(dataDir, 'DOCKER_VERSION')
    with open(path) as f:
        return f.read().replace('\n', '')

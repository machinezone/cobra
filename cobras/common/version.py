'''Compute our version number

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import pkg_resources


def getVersion(module=None):
    '''Get our own version using pkg_resources'''

    if module is None:
        module = 'cobras'

    return pkg_resources.get_distribution(module).version

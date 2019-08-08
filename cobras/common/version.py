'''Compute our version number

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import pkg_resources

from cobras.common.memoize import memoize


def getVersion():
    '''Get our own version using pkg_resources'''

    return pkg_resources.get_distribution("cobras").version

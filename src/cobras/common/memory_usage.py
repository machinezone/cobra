'''Capture memory usage

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import os

import psutil

from cobras.common.memoize import memoize


@memoize
def getContainerMemoryLimit():
    '''In bytes'''

    path = '/sys/fs/cgroup/memory/memory.limit_in_bytes'
    if not os.path.exists(path):
        return psutil.virtual_memory().total
    else:
        with open(path) as f:
            mem = f.read()
            return int(mem)


def getProcessUsedMemory():
    p = psutil.Process()
    return p.memory_info().rss

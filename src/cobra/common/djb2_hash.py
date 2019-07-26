'''djb2 hash (unsused)

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''


def djb2Hash(data):
    '''Return a 32 bits digest'''

    hash = 5381
    for x in data:
        hash = ((hash << 5) + hash) + ord(x)
    return hash & 0xFFFFFFFF

'''Misc algorithm routines

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''


def transpose(entries):
    '''Transpose a matrix'''

    # Lame fix
    if isinstance(entries, list) and len(entries) == 1 and entries[0] is None:
        return []

    return list(map(list, zip(*entries)))

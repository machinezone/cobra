'''Misc algorithm routines

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''


def transpose(entries):
    '''Transpose a matrix'''

    # Lame fix
    if isinstance(entries, list) and len(entries) == 1 and entries[0] is None:
        return []

    return list(map(list, zip(*entries)))


def extractAttributeFromDict(subtree, attribute):
    '''extract a subfield'''
    if subtree is None:
        return subtree

    fieldsComponents = attribute.split('.')
    for component in fieldsComponents:
        subtree = subtree.get(component, {}) or {}

    return subtree

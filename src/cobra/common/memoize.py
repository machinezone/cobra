'''Memoization decorator for functions taking one or more arguments.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''


def memoize(f):
    """Memoization decorator for functions taking one or more arguments."""

    class Memodict(dict):
        '''Helper class derived from dict'''

        def __init__(self, f):
            '''Constructor'''

            dict.__init__(self)
            self.f = f

        def __call__(self, *args):
            '''Call function'''

            return self[args]

        def __missing__(self, key):
            '''Missing method'''

            ret = self[key] = self.f(*key)
            return ret

    return Memodict(f)

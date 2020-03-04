'''python profiler that gets executed when an app terminates

Copyright (c) 2020 Machine Zone, Inc. All rights reserved.
'''

import io
import pstats
import atexit
import cProfile


def reportProfilerOutput(pr):
    '''
    See
    https://docs.python.org/3/library/profile.html
    https://docs.python.org/3/library/atexit.html
    '''
    s = io.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print(s.getvalue())


def registerProfiler():
    '''Enable profiling and register an atexit handler which will print
    profiling data when the app terminates.'''

    pr = cProfile.Profile()
    pr.enable()
    atexit.register(reportProfilerOutput, pr)

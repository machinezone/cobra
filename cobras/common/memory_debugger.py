'''Track memory usage

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

https://blog.fugue.co/2017-03-06-diagnosing-and-fixing-memory-leaks-in-python.html  # noqa
'''

import asyncio
import gc
import sys
import tracemalloc
from tracemalloc import Filter

import byteformat
import psutil

DEFAULT_DURATION = 5


class MemoryDebugger():
    def __init__(self, duration=None, steps=None, mode=None):
        tracemalloc.start(10)

        self.duration = duration
        if duration is None:
            self.duration = DEFAULT_DURATION

        self.mode = mode
        if mode is None:
            self.mode = 'filename'  # or traceback, or lineno
            self.mode = 'traceback'  # or traceback, or lineno

        self.steps = steps
        self.stop = False

        self.snapshots = []
        self.filters = [Filter(inclusive=True, filename_pattern="**")]
        self.p = psutil.Process()

        self.printAllTasks = False

    def collect_stats(self):
        self.snapshots.append(tracemalloc.take_snapshot())

        if len(self.snapshots) < 2:
            return
        else:
            # Only keep the last 2 elements
            self.snapshots = self.snapshots[-2:]

        old_snapshot = self.snapshots[-2]
        snapshot = self.snapshots[-1]
        kind = self.mode
        stats = snapshot.filter_traces(self.filters).compare_to(
                    old_snapshot.filter_traces(self.filters), kind)

        print('\n\n== Memory report ==')
        for stat in stats[:10]:
            fmt = "{} new {} total / {} new {} total memory blocks: "
            print(fmt.format(byteformat.format(stat.size_diff),
                             byteformat.format(stat.size),
                             stat.count_diff,
                             stat.count))
            for line in stat.traceback.format():
                print(line)
            print()

    def printTasksStats(self):
        tasks = asyncio.all_tasks()
        print('#{} tasks'.format(len(tasks)))

        if self.printAllTasks:
            for task in tasks:
                print(task)
                print()
        print()

    def analyzeGarbage(self):
        '''Garbage seems to be constant, so we should not worry about it

        # Add this at the start of your program
        import gc
        gc.set_debug(gc.DEBUG_SAVEALL)
        '''

        gc.collect()
        garbage = []
        for item in gc.garbage:
            garbage.append(sys.getsizeof(item))

        garbage.sort()
        print(garbage)
        print(sum(garbage))

    async def run(self):
        i = 0
        while True:
            # gc.collect()
            print('RSS: ' + byteformat.format(self.p.memory_info().rss))
            # Comment the next line to get a very simple mem print
            self.collect_stats()
            self.printTasksStats()

            if self.steps is not None and i == self.steps:
                return

            i += 1

            # Sleep
            await asyncio.sleep(self.duration)

            if self.stop:
                return

    def terminate(self):
        self.stop = True

'''Utility for batch publishing.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

FIXME: Should be renamed
'''

import json


def computeEventTimeDeltas(events: str) -> list:

    lines = events.splitlines()
    N = len(lines)
    assert N > 0, 'event list should not be empty'

    events = [json.loads(line) for line in lines]

    deltas = []
    for i in range(1, N):
        previousTs = events[i - 1]['timestamp']
        currentTs = events[i]['timestamp']
        delta = currentTs - previousTs

        deltas.append((lines[i - 1], delta))

    deltas.append((lines[N-1], 0))

    return deltas

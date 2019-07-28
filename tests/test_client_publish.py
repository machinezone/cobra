'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

import os

from cobras.client.publish import computeEventTimeDeltas


def test_computeEventTimeDeltas():
    root = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(root, 'test_data', 'client_publish', '54_events.jsonl')

    with open(path) as f:
        events = f.read()

        lines = events.splitlines()
        N = len(lines)

        eventsWithDeltas = computeEventTimeDeltas(events)

        assert N == len(eventsWithDeltas)

        assert eventsWithDeltas[0][1] == 17
        assert eventsWithDeltas[12][1] == 0
        assert eventsWithDeltas[15][1] == 341

    path = os.path.join(root, 'test_data', 'client_publish', '1_event.jsonl')

    with open(path) as f:
        events = f.read()

        lines = events.splitlines()
        N = len(lines)

        eventsWithDeltas = computeEventTimeDeltas(events)

        assert N == len(eventsWithDeltas)

        assert eventsWithDeltas[0][1] == 0

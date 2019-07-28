'''Subscribe to custom channels that let us monitor cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import collections
import json

import byteformat
import click
import tabulate

from cobras.client.client import subscribeClient
from cobras.common.algorithm import transpose
from cobras.common.throttle import Throttle
from cobras.server.stats import DEFAULT_STATS_CHANNEL


def writeJson(data):
    '''JSON Pretty printer'''

    return json.dumps(data, sort_keys=True,
                      indent=4, separators=(',', ': '))


class MessageHandlerClass:
    def __init__(self, websockets, args):
        self.cnt = 0
        self.throttle = Throttle(seconds=1)
        self.resetMetrics()

        self.raw = args['raw']
        self.roleFilter = args['role_filter']
        self.showNodes = args['show_nodes']
        self.subscribers = args['subscribers']

        self.roleMetrics = []

    def resetMetrics(self):
        self.metrics = collections.defaultdict(int)
        self.nodes = set()

        self.nodeEntries = []
        self.nodeEntriesHeader = None

        self.allRoleMetrics = {}
        self.roles = set()

    async def on_init(self):
        pass

    def humanReadableSize(self, key, val):
        return byteformat.format(val) if '_bytes' in key else val

    def shouldProcessNode(self, node):
        return 'subscriber' in node if self.subscribers else True

    async def handleMsg(self, msg: str) -> bool:

        data = json.loads(msg)['body']['messages'][0]
        node = data['node']

        if node not in self.nodes and self.shouldProcessNode(node):
            # nodeEntry = [data['node'][:8]]
            nodeEntry = [node]
            nodeEntryHeaders = ['Nodes']

            cobraData = data['data']['cobra']
            for key in sorted(cobraData.keys()):
                s = sum(cobraData[key].values())
                self.metrics[key] += s

                s = self.humanReadableSize(key, s)

                nodeEntry.append(s)
                nodeEntryHeaders.append(key)

            self.updateRoleMetrics(cobraData)

            # System stats
            for metric in data['data']['system'].keys():
                val = data['data']['system'][metric]

                if metric == 'connections':
                    self.metrics[metric] += val

                nodeEntryHeaders.append(metric)

                val = self.humanReadableSize(metric, val)

                nodeEntry.append(val)

            self.nodeEntries.append(nodeEntry)

            self.nodes.add(node)

            if self.nodeEntriesHeader is None:
                self.nodeEntriesHeader = nodeEntryHeaders

        if self.throttle.exceedRate():
            return True

        click.clear()
        # print(yaml.dump(data))

        self.metrics = {key: self.humanReadableSize(key, val)
                        for key, val in self.metrics.items()}

        print(writeJson(self.metrics))
        print()

        # Print a table with all nodes
        nodeEntries = [self.nodeEntriesHeader]
        self.nodeEntries.sort()
        nodeEntries.extend(self.nodeEntries)

        # Transpose our array and print the nodes horizontally
        if 0 < len(nodeEntries) < 8:
            nodeEntries = transpose(nodeEntries)

        if self.showNodes:
            print(tabulate.tabulate(nodeEntries,
                                    tablefmt="simple",
                                    headers="firstrow"))

        self.displayRoleMetrics()

        self.resetMetrics()
        return True

    def updateRoleMetrics(self, cobraData):
        '''Collect data per role'''

        for metric, metricData in cobraData.items():

            metricByRole = self.allRoleMetrics.get(metric)
            if metricByRole is None:
                metricByRole = collections.defaultdict(int)

            for role, val in metricData.items():
                metricByRole[role] += val

                if self.roleFilter is not None:
                    if self.roleFilter in role:
                        self.roles.add(role)
                else:
                    self.roles.add(role)

            self.allRoleMetrics[metric] = metricByRole

        if self.raw:
            print(cobraData)

    def displayRoleMetrics(self):
        '''Display data broken down per role'''

        rows = [['Roles'] + list(sorted(self.roles))]

        for metric in sorted(self.allRoleMetrics):
            metricByRole = self.allRoleMetrics[metric]
            # print(metric, metricByRole)

            row = [metric]

            for role in sorted(self.roles):
                val = metricByRole.get(role, 0)

                val = self.humanReadableSize(metric, val)

                row.append(val)

            rows.append(row)

        print()
        print(tabulate.tabulate(rows,
                                tablefmt="simple",
                                headers="firstrow"))


def runMonitor(url, credentials, raw, roleFilter, showNodes, subscribers):
    asyncio.get_event_loop().run_until_complete(
            subscribeClient(url, credentials, DEFAULT_STATS_CHANNEL,
                            '', MessageHandlerClass,
                            {'raw': raw,
                             'role_filter': roleFilter,
                             'show_nodes': showNodes,
                             'subscribers': subscribers}))

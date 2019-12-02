'''Subscribe to custom channels that let us monitor cobra

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import asyncio
import collections
import rapidjson as json
import os
from typing import Dict, List

import click
import humanfriendly
import tabulate
from cobras.client.client import subscribeClient, unsafeSubcribeClient
from cobras.client.connection import ActionFlow
from cobras.common.algorithm import transpose
from cobras.common.apps_config import STATS_APPKEY
from cobras.common.throttle import Throttle
from cobras.server.stats import DEFAULT_STATS_CHANNEL


def getDefaultMonitorUrl(host=None, port=None):
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = os.getenv('COBRA_PORT', 8765)

    return f'ws://{host}:{port}/v2?appkey={STATS_APPKEY}'


def writeJson(data):
    '''JSON Pretty printer'''

    return json.dumps(data, sort_keys=True, indent=4)


class MessageHandlerClass:
    def __init__(self, websockets, args):
        self.cnt = 0
        self.throttle = Throttle(seconds=1)
        self.resetMetrics()

        self.raw = args['raw']
        self.roleFilter = args['role_filter']
        self.channelFilter = args['channel_filter']
        self.showNodes = args['show_nodes']
        self.showRoles = args['show_roles']
        self.showChannels = args['show_channels']
        self.subscribers = args['subscribers']
        self.system = args['system']
        self.once = args['once']

        self.roleMetrics = []

    def resetMetrics(self):
        self.metrics = collections.defaultdict(int)
        self.nodes = set()

        self.nodeEntries = []
        self.nodeEntriesHeader = None

        self.allRoleMetrics = {}
        self.roles = set()

        self.allChannelMetrics = {}
        self.channels = set()

    async def on_init(self):
        pass

    def humanReadableSize(self, key, val):
        return humanfriendly.format_size(val) if '_bytes' in key else val

    def shouldProcessNode(self, node):
        return 'subscriber' in node if self.subscribers else True

    async def handleMsg(self, messages: List[Dict], position: str) -> ActionFlow:

        message = messages[0]
        data = message
        node = data['node']

        if node not in self.nodes and self.shouldProcessNode(node):
            # nodeEntry = [data['node'][:8]]
            nodeEntry = [node]
            nodeEntryHeaders = ['Nodes']

            cobraData = data['data']['cobra']
            for key in sorted(cobraData.keys()):

                if self.system:
                    skip = False
                    for keyName in ('published', 'subscribed', 'subscriptions'):
                        if keyName in key:
                            skip = True
                    if skip:
                        continue

                s = sum(cobraData[key].values())
                self.metrics[key] += s

                s = self.humanReadableSize(key, s)

                nodeEntry.append(s)
                nodeEntryHeaders.append(key)

            self.updateRoleMetrics(cobraData)

            channelData = data['data'].get('channel_data')
            if channelData is not None:
                self.updateChannelMetrics(channelData)

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
            return ActionFlow.CONTINUE

        click.clear()
        # print(yaml.dump(data))

        self.metrics = {
            key: self.humanReadableSize(key, val) for key, val in self.metrics.items()
        }

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
            print(tabulate.tabulate(nodeEntries, tablefmt="simple", headers="firstrow"))

        if self.showRoles:
            self.displayRoleMetrics()

        if self.showChannels:
            self.displayChannelMetrics()

        self.resetMetrics()
        return ActionFlow.STOP if self.once else ActionFlow.CONTINUE

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
        print(tabulate.tabulate(rows, tablefmt="simple", headers="firstrow"))

    def updateChannelMetrics(self, cobraData):
        '''Collect data per channel'''
        for metric, metricData in cobraData.items():

            metricByChannel = self.allChannelMetrics.get(metric)
            if metricByChannel is None:
                metricByChannel = collections.defaultdict(int)

            for channel, val in metricData.items():
                metricByChannel[channel] += val

                if self.channelFilter is not None:
                    if self.channelFilter in channel:
                        self.channels.add(channel)
                else:
                    self.channels.add(channel)

            self.allChannelMetrics[metric] = metricByChannel

        if self.raw:
            print(cobraData)

    def displayChannelMetrics(self):
        rows = [['Channels'] + list(sorted(self.channels))]

        for metric in sorted(self.allChannelMetrics):
            metricByChannel = self.allChannelMetrics[metric]
            # print(metric, metricByRole)

            row = [metric]

            for channel in sorted(self.channels):
                val = metricByChannel.get(channel, 0)

                val = self.humanReadableSize(metric, val)

                row.append(val)

            rows.append(row)

        rows = transpose(rows)

        print()
        print(tabulate.tabulate(rows, tablefmt="simple", headers="firstrow"))


def runMonitor(
    url,
    credentials,
    raw,
    roleFilter,
    channelFilter,
    showNodes,
    showRoles,
    showChannels,
    subscribers,
    system,
    once,
    retry=True,
):
    position = None

    handler = unsafeSubcribeClient
    if retry:
        handler = subscribeClient

    messageHandler = asyncio.get_event_loop().run_until_complete(
        handler(
            url,
            credentials,
            DEFAULT_STATS_CHANNEL,
            position,
            '',
            MessageHandlerClass,
            {
                'raw': raw,
                'role_filter': roleFilter,
                'channel_filter': channelFilter,
                'show_nodes': showNodes,
                'show_roles': showRoles,
                'show_channels': showChannels,
                'subscribers': subscribers,
                'system': system,
                'once': once,
            },
        )
    )
    return messageHandler

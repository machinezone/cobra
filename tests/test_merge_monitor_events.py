'''Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.'''

eventB = '''
data:
  cobra:
    connections: 1
    published_bytes: {eeeeeeeeeeeeeeeeffffffffffffffff: 4850623, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 6920}
    published_bytes_per_second: {eeeeeeeeeeeeeeeeffffffffffffffff: 309003, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 173}
    published_count: {eeeeeeeeeeeeeeeeffffffffffffffff: 4570, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 40}
    published_count_per_second: {eeeeeeeeeeeeeeeeffffffffffffffff: 292, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 1}
    subscribed_bytes: {AAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB: 1527273, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 6920}
    subscribed_bytes_per_second: {EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 173}
    subscribed_count: {AAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB: 2255, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 40}
    subscribed_count_per_second: {EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 1}
    subscriptions: {AAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB: 0, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 0}
  system: {cpu_percent: 12.7, mem: 27840, utime: 4.781467}
node: 5521e5e0854648068967c6d2cf6b44e8
'''

eventA = '''
data:
  cobra:
    connections: 1
    published_bytes: {eeeeeeeeeeeeeeeeffffffffffffffff: 57683990, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 10034}
    published_bytes_per_second: {eeeeeeeeeeeeeeeeffffffffffffffff: 405655}
    published_count: {eeeeeeeeeeeeeeeeffffffffffffffff: 53783, EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 58}
    published_count_per_second: {eeeeeeeeeeeeeeeeffffffffffffffff: 381}
    subscribed_bytes: {EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 10034}
    subscribed_bytes_per_second: {}
    subscribed_count: {EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 58}
    subscribed_count_per_second: {}
    subscriptions: {EEEEEEEEEEEEEEEEFFFFFFFFFFFFFFFF: 0}
  system: {cpu_percent: 7.5, mem: 28656, utime: 16.944766}
node: 0e69e8d19f8c47e795cb129176e5ca65
'''

import yaml

dataA = yaml.load(eventA, Loader=yaml.FullLoader)
dataB = yaml.load(eventB, Loader=yaml.FullLoader)


class Foo():
    def __init__(self):
        self.data = {}
        self.entries = [(('Node', 'Connections', 'Published bytes',
                          'Published bytes per second', 'Published count'))]

    def add(self, data):
        for key in data.keys():
            if isinstance(data[key], dict):
                print(sum(data[key].values()))

                self.data[key] = sum(data[key].values())

    def dump(self):
        # click.echo(tabulate.tabulate(self.entries, tablefmt="simple", headers="firstrow"))
        print(yaml.dump({"data": self.data}))


def test_merge_monitor_events():
    foo = Foo()
    foo.add(dataA['data']['cobra'])
    foo.add(dataB['data']['cobra'])
    foo.dump()

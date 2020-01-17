import os
import time
import random
import collections
from subprocess import Popen, PIPE, STDOUT


ClusterNode = collections.namedtuple(
    'ClusterNode', ['node_id', 'address', 'ip', 'port', 'role']
)


def execCommand(cmd, host, port):
    # output = os.popen(f'redis-cli -h {host} -p {port} ' + cmd).read()
    p = Popen(['redis-cli', '-h', host, '-p', str(port)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    output = p.communicate(input=cmd.encode())[0]
    print(output)
    return output.decode()


def getIp(host):
    '''
    $ getent hosts localhost
    127.0.0.1	localhost

    >>> import socket
    >>> socket.gethostbyname_ex('localhost')
    ('localhost', [], ['127.0.0.1'])
    '''
    import socket
    return socket.gethostbyname_ex(host)[2][0]


def meet(nodes):
    N = len(nodes) - 1
    for i in range(N):
        host1, port1 = nodes[i]
        ip1 = getIp(host1)

        host2, port2 = nodes[i+1]
        ip2 = getIp(host2)

        execCommand(f'cluster meet {ip2} {port2}', ip1, port1)

    time.sleep(2)


def get_nodes(node, port):
    ip = getIp(node)
    # it would be best not to parse stdout to capture this
    return execCommand(f'cluster nodes', node, port)


def get_nodes_as_list(node, port):
    nodes_as_text = get_nodes(node, port)

    nodes = []
    for line in nodes_as_text.splitlines():
        tokens = line.split()
        node_id = tokens[0]

        address = tokens[1]
        url, _, _ = address.partition('@')
        ip, _, port = url.partition(':')

        role = tokens[2]
        role = role.replace('myself,', '')
        role = role.replace('myself,', '')

        nodes.append(ClusterNode(node_id, address, ip, port, role))

    return nodes


def set_replicas(nodesInfo):
    N = len(nodesInfo) // 2
    assert len(nodesInfo) % 2 == 0

    for i in range(N):
        ip1 = nodesInfo[i].ip
        port1 = nodesInfo[i].port

        nodeid = nodesInfo[i+N].node_id

        execCommand(f'cluster flushslots', ip1, port1)
        execCommand(f'cluster replicate {nodeid}', ip1, port1)

    time.sleep(1)


def getMasters(nodesInfo):
    masters = []
    for nodeInfo in nodesInfo:
        if nodeInfo.role == 'master':
            print(nodeInfo.node_id, nodeInfo.address, nodeInfo.ip, nodeInfo.port)

            # execCommand(f'cluster replicate {nodeid}', ip1, port1)

        masters.append(nodeInfo)

    return masters


def set_slots(nodes, nodesInfo):
    masters = getMasters(nodesInfo)

    slots_by_master = collections.defaultdict(list)

    for i in range(16384):
        master = random.choice(masters)
        slots_by_master[master].append(str(i))

    i = 0
    for master, slots in slots_by_master.items():
        for slot in slots:
            cmd = f'CLUSTER ADDSLOTS {slot}'
            execCommand(cmd, master.ip, master.port)

            print(i, 16384)
            i += 1


nodes = [
    ['localhost', 10000],
    ['localhost', 10001],
    ['localhost', 10002],
    ['localhost', 10003],
    ['localhost', 10004],
    ['localhost', 10005],
]

meet(nodes)

nodesInfo = get_nodes_as_list(nodes[0][0], nodes[0][1])
for node in nodesInfo:
    print(node)

set_replicas(nodesInfo)
# get_nodes(nodes[0][0], nodes[0][1])

# #nodesInfo = get_nodes_as_list(nodes[0][0], nodes[0][1])
# #nodeIds = [node.node_id for node in nodesInfo]
# #set_replicas(nodes, nodeIds)
# 
# nodesInfo = get_nodes_as_list(nodes[0][0], nodes[0][1])
# for node in nodesInfo:
#     print(node)
# 
# set_slots(nodes, nodesInfo)

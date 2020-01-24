#!/bin/sh

nodes="www.google.com"
nodes="localhost localhost"
nodes="redis11 redis12 redis13 redis14 redis15 redis16 redis17 redis18"
nodes="redis1 redis2 redis3 redis4 redis5 redis6"
nodes="localhost:10000 localhost:10001 localhost:10002 localhost:10003 localhost:10004 localhost:10005"

ips=""
OS=`uname`

for node in $nodes
do
    host=`echo $node | awk -F: '{print $1}'`
    port=`echo $node | awk -F: '{print $2}'`

    echo Resolving address for host $node
    if test $OS = Darwin ; then
        # nslookup gives weird results on Linux
        ip=`nslookup $host | grep '^Address' | awk 'NR == 2 { print $2 }'`
    else
        # getent is a shell builtin on osx and
        # cannot be used from a shell (event with 'eval')
        ip=`getent hosts $host | awk '{print $1}'`
    fi
    echo $host resolve to $ip
    ips="$ips $ip:$port"

    redis-cli -h $host -p $port FLUSHDB
    redis-cli -h $host -p $port CLUSTER RESET
done

redis-cli -h $host -p $port --cluster create $ips --cluster-replicas 1

# Adding host
# redis-cli -p 10000 --cluster add-node 127.0.0.1:10006 127.0.0.1:10000

# Adding a host as a replica
# redis-cli -p 10000 --cluster add-node --cluster-slave 127.0.0.1:10007 127.0.0.1:10000

# Reshard
# redis-cli -p 10000 --cluster reshard 127.0.0.1:10006

# Rebalance slots accross nodes
# redis-cli -p 10000 --cluster rebalance 127.0.0.1:10007

# Delete node
# redis-cli -p 10000 --cluster del-node 127.0.0.1:10007 964755107923d607b544db0b5cde96fd8d210294

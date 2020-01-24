#!/bin/sh

nodes="www.google.com"
nodes="localhost localhost"
nodes="redis11 redis12 redis13 redis14 redis15 redis16 redis17 redis18"
nodes="redis1 redis2 redis3 redis4 redis5 redis6"

ips=""

for node in $nodes
do
    echo Resolving address for host $node
    # ip=`nslookup $node | grep '^Address' | awk 'NR == 2 { print $2 }'`
    ip=`getent hosts redis1 | awk '{print $1}'
    echo $node resolve to $ip
    ips="$ips $ip:6379"

    redis-cli -h $node FLUSHDB
    redis-cli -h $node CLUSTER RESET
done

redis-cli --cluster create $ips --cluster-replicas 1

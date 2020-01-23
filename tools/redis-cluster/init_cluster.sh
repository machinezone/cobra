#!/bin/sh

nodes="www.google.com"
nodes="redis11 redis12 redis13 redis14 redis15 redis16 redis17 redis18"
nodes="localhost localhost"

ips=""

for node in $nodes
do
    ip=`nslookup $node | grep '^Address' | awk 'NR == 2 { print $2 }'`
    echo $node resolve to $ip
    ips="$ips $ip:6379"
done

redis-cli --cluster create $ips --cluster-replicas 1

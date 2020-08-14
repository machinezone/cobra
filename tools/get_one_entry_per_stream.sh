#!/bin/sh

hosts="
redis-cluster-0
redis-cluster-12
redis-cluster-3
redis-cluster-5
redis-cluster-6
redis-cluster-7
redis-cluster-8"

for host in $hosts
do
    keys=`oc rsh $host redis-cli KEYS \* | awk '{print $2}' | tr -d '"' | tr -d '\n'`
    for key in $keys
    do
        echo "oc rsh $host redis-cli -c XRANGE $key - + COUNT 1"
    done
done


#!/bin/sh

hosts="
redis-cluster-0  
redis-cluster-1 
redis-cluster-10
redis-cluster-11
redis-cluster-12
redis-cluster-13
redis-cluster-2
redis-cluster-3
redis-cluster-4
redis-cluster-5
redis-cluster-6
redis-cluster-7
redis-cluster-8
redis-cluster-9"

hosts=`oc get pods | grep redis-cluster | awk '{print $1}'`

for host in $hosts
do
    oc rsh $host redis-cli INFO | grep -q role:master && echo $host
done

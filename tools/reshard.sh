#!/bin/sh

nodes=`rcc cluster-nodes --redis_urls redis://localhost:11000 | awk '/master/ {print $1}'`

for node in $nodes ; do
    echo $node
    rcc binpacking-reshard --redis_urls redis://localhost:11001 -w weights.csv --node_id $node
    sleep 5
done

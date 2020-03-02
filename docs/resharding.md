# Using rcc to reshard a redis cluster using keyspace notification

<img src="pie.jpg" />

## Introduction

[rcc](https://github.com/machinezone/rcc/) comes with 2 important tools, one for analyzing the keys access accross nodes, built on top of [redis keyspace notifications](https://redis.io/topics/notifications) (which in turns runs on top of redis PubSub). The instrumentation is done over a period of time to sample the key access patterns. A 'weights' file is created as part of this tool. That file is saved in the current working directory by default. It is a very simple csv file that show how often a key is accessed. Currently rcc only support tracking *XADD* redis commands.

```
$ head weights.csv
_pubsub::foo,50
_pubsub::bar,53
_pubsub::baz,7
_pubsub::buz,19
_pubsub::blah,940
_pubsub::blooh,20
_pubsub::xxx,552
_pubsub::yyy,571
_pubsub::zzz,92
_pubsub::foo,5035
```

The second tool is used to reshard a cluster, and migrate slots to node using the bin-packing algorithm. To feed this algorithm, weights are required.

### Generating redis cluster traffic.

We use the `cobra publish` in batch mode command to send data to [cobra](https://github.com/machinezone/rcc/), which internally send lots of XADD commands to our redis cluster.

* Cobra server started with: `cobra run -r redis://localhost:11000`
* Cobra publishers: cobra publish --batch

The redis cluster is started with: `rcc make-cluster` ; rcc has a convenience sub-command to generate config file for cluster (by default 3 masters and 3 replicas), and finally initialize the cluster.

### Keyspace access analysis before resharding

```
rcc analyze-keyspace --redis_url redis://localhost:11000 --timeout 10
...
== Nodes ==
# each ∎ represents a count of 105. total 15515
127.0.0.1:11000 [  6789] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
127.0.0.1:11002 [  4983] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
127.0.0.1:11001 [  3743] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
```

### Resharding

```
$ rcc reshard --redis_url redis://localhost:11000
file descriptors ulimit: 1024
resharding can be hungry, bump it with ulimit -n if needed
== f3fa13802f339abb98ccb377e8a1a4eb957be987 / 127.0.0.1:11000 ==
migrated 0 slots
Waiting for cluster view to be consistent...
.== 8c67b776ab52ad756777866dcb8425cc866c71a3 / 127.0.0.1:11001 ==
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrated 10 slots
Waiting for cluster view to be consistent...
............== d50246e7e3914639759add181c71a2e3c879ed2f / 127.0.0.1:11002 ==
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrating 1 keys
migrated 11 slots
Waiting for cluster view to be consistent...
.....total migrated slots: 11
```

It roughtly looks like we took slots away from the first node, and gave them to the other two redis instances.

### Keyspace access analysis after resharding

```
rcc analyze-keyspace --redis_url redis://localhost:11000 --timeout 10
...
== Nodes ==
# each ∎ represents a count of 79. total 15114
127.0.0.1:11002 [  5087] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
127.0.0.1:11000 [  5040] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
127.0.0.1:11001 [  4987] ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎
```

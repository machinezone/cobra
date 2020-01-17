
## Cluster

bind to 0.0.0.0

easier to send 

* cluster meet
* cluster replica

Service needs to open both ports

New cobra instance

We used the --disable-multiplexing option.
To see executed query we used --log-leve debug + --dump-queries

## redis-cluster-proxy

Debugging arguments

```
      - args:
        - --disable-multiplexing
        - always
        - --threads
        - "8"
        - --log-level
        - debug
        - --dump-queries
        - --dump-buffer
        - --dump-queues
        - 1.2.3.4:6379
```

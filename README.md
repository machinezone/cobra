# General

Cobra is a realtime messaging server using Python3, WebSockets and Redis PubSub. It was presented in great details during [RedisConf 2019](https://events.redislabs.com/redis-conf/redis-conf-2019/).

* [slides](https://bsergean.github.io/redis_conf_2019/slides.html)
* [youtube](https://www.youtube.com/watch?v=o8CC8qYfRQE&t=147s)

# Installation

To setup cobra run those commands:

```
git clone <url>
cd cobra
python3 -m venv venv
source venv/bin/activate
make dev
make test
```

# Usage

```
$ cobra
Usage: cobra [OPTIONS] COMMAND [ARGS]...

  Cobra is a realtime messaging server using Python3, WebSockets and Redis
  PubSub.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  admin         Run admin commands.
  health        Health check
  init          Setup cobra
  monitor       Monitor cobra
  publish       Publish to a channel
  run           Run the cobra server
  secret        Generate secrets used for authentication...
  subscribe     Subscribe to a channel (with redis)
  ws_subscribe  Publish to a channel
```

To run the server use `cobra run`. You can run a health-check against the server with `cobra health`.

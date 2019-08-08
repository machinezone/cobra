# General

Cobra is a realtime messaging server using Python3, WebSockets and Redis PubSub. It was presented in great details during [RedisConf 2019](https://events.redislabs.com/redis-conf/redis-conf-2019/).

* [slides](https://bsergean.github.io/redis_conf_2019/slides.html)
* [youtube](https://www.youtube.com/watch?v=o8CC8qYfRQE&t=147s)

Cobra has been used in production receiving heavy traffic for about a year. Since it was written in Python it was named after a snake as an hommage to a great programming language.

# News

Cobra is actively being developed, check out the [changelog](CHANGELOG.md) to know what's cooking.

# Installation

## With pip

```
pip install cobras
```

## With docker

```
docker pull bsergean/cobra
```

## For development

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
  admin            Run admin commands.
  health           Health check
  init             Setup cobra
  monitor          Monitor cobra
  publish          Publish to a channel
  run              Run the cobra server
  redis_subscribe  Subscribe to a channel (with redis)
  subscribe        Subscribe to a channel
  secret           Generate secrets used for authentication...
```

To run the server use `cobra run`. You can run a health-check against the server with `cobra health`.

```
cobra health --url 'ws://jeanserge.com/v2?appkey=_health' --secret A5a3BdEfbc6Df5AAFFcadE7F9Dd7F17E --role health
```

# Setup

To run in production you will need a redis instance, with version > 5 since redis is using [Streams](https://redis.io/topics/streams-intro). Here are 
environment variables that you will likely want to tweak. Here we use 2 redis instances, and we bind on 0.0.0.0 so that the internet can see us.

```
- name: COBRA_HOST
  value: 0.0.0.0
- name: COBRA_REDIS_URLS
  value: redis://redis1;redis://redis2
```

# Thank you

There would be no cobra without some other amazing open-source projects and tech.

- [Python](https://www.python.org/) (and [asyncio](https://realpython.com/async-io-python/), one of the killer python3 feature !)
- [Redis](https://redis.io/), the swiss army knife of the internet which provide a very scalable publish/subscribe to dispatch messages.
- The python [websockets](https://websockets.readthedocs.io/en/stable/intro.html) library, very elegantly implementing the [WebSockets](https://tools.ietf.org/html/rfc6455) protocol.

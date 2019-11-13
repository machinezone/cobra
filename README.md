# General

[![PyPI version](https://badge.fury.io/py/cobras.svg)](https://badge.fury.io/py/cobras)
[![Build Status](https://travis-ci.org/machinezone/cobra.svg?branch=master)](https://travis-ci.org/machinezone/cobra)
[![PyPI Python Versions](https://img.shields.io/pypi/pyversions/cobras.svg)](https://img.shields.io/pypi/pyversions/cobras)
[![License](https://img.shields.io/pypi/l/cobras.svg)](https://img.shields.io/pypi/l/cobras)
[![Wheel](https://img.shields.io/pypi/wheel/cobras.svg)](https://img.shields.io/pypi/wheel/cobras)
[![codecov](https://codecov.io/gh/machinezone/cobra/branch/master/graph/badge.svg)](https://codecov.io/gh/machinezone/cobra)

Cobra is a realtime messaging server using Python3, WebSockets and Redis Streams. It was presented in great details during [RedisConf 2019](https://events.redislabs.com/redis-conf/redis-conf-2019/). Since then we've added history support which let cobra retain messages published to a channel that no-one is subscribed to. This makes it easier to blow up your systems through [OOMs](https://en.wikipedia.org/wiki/Out_of_memory) and fill your hard drives, but it makes cobra much more useful.

* [slides](https://bsergean.github.io/redis_conf_2019/slides.html)
* [youtube](https://www.youtube.com/watch?v=o8CC8qYfRQE&t=147s)

[![Alt text](https://image.slidesharecdn.com/06benjaminsergeant-190507205253/95/real-time-health-analytics-with-websockets-python-3-and-redis-pubsub-benjamin-sergeant-1-638.jpg)](https://www.youtube.com/watch?v=o8CC8qYfRQE)

Cobra has been used in production receiving heavy traffic for about a year. Since it was written in Python it was named after a snake as an hommage to a great programming language.

There are 4 operations that a client can execute against a cobra server: *publish*, *subscribe*, *read* and *write*. *publish* and *subscribe* are the 2 operations core to a group-chat. *read* and *write* are the typical operations that key value stores (such as memcached), or a python dictionnary provide.

* *publish*: send data to a channel, which will be broadcasted to anyone subscribed to that channel
* *subscribe*: receive events sent to a channel in real time.
* *write*: record some data (addressed by a key)
* *read*: retrieve data

Interested ? Go read the [docs](https://machinezone.github.io/cobra/) ! If things don't work as expected, please create an issue in github, or even better a pull request if you know how to fix your problem.

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

## Cobra server and test clients

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

## bavarde

*bavarde* is a chat client that runs against the public cobra server. Bring up 2 terminals, runs the 2 commands below and start typing.

```
$ bavarde client
...
```

```
$ bavarde client --username bob
...
```


# Setup

`cobras init` needs to be run once to generate an app configuration file, in `~/.cobra.yaml`. That file contains all the roles, secrets and apps configured. Clients will use this data to authenticate.

To run in production you will need a redis (version > 5) instance. Here are environment variables that you will likely want to tweak, to connect to 2 redis instances (for scalabity), and to bind on 0.0.0.0 so that the internet can see your instance.

```
- name: COBRA_HOST
  value: 0.0.0.0
- name: COBRA_REDIS_URLS
  value: redis://redis1;redis://redis2

# config can be a path to a file
- name: COBRA_APPS_CONFIG_PATH
  value: /path/to/your/cobra.yaml

# config can be a blob of gziped + base64 data (if you do not want to mount volumes)
# Generate it with:
# `gzip -c ~/.cobra.yaml | base64`
- name: COBRA_APPS_CONFIG_CONTENT
  value: BIGBLOGOFDATA
```

# Thank you

There would be no cobra without some other amazing open-source projects and tech. Here are 3 very remarkable ones.

- [Python](https://www.python.org/) (and [asyncio](https://realpython.com/async-io-python/), one of the killer python3 feature !)
- [Redis](https://redis.io/), the swiss army knife of the internet which provide a very scalable publish/subscribe feature to dispatch messages while retaining them and allowing lookups of old messages (see [Redis Streams] (https://redis.io/topics/streams-intro).
- The python [websockets](https://websockets.readthedocs.io/en/stable/intro.html) library, very elegantly implementing the [WebSockets](https://tools.ietf.org/html/rfc6455) protocol using **asyncio**.
- The python [aioredis](https://aioredis.readthedocs.io/en/v1.2.0/) library used to talk to Redis. This [redis labs](https://redislabs.com/blog/async-await-programming-basics-python-examples/) article explains some pitfalls with asyncio and how to get the best performance out of it.

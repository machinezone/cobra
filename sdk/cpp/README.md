## C++ cobra sdk

# Requirements

Install cmake, conan, ninja and a C++ compiler (XCode/clang or gcc or ...).

# Build

1. mkdir build
2. cd build
3. conan install .. # build packages as needed, see output
4. cmake -GNinja ..
5. ninja

# Usage

```
$ bin/cobra_cli --help
ws is a websocket tool
Usage: bin/cobra_cli [OPTIONS] [SUBCOMMAND]

Options:
  -h,--help                   Print this help message and exit
  --version                   Print ws version
  --logfile TEXT              path where all logs will be redirected

Subcommands:
  cobra_subscribe             Cobra subscriber
  cobra_publish               Cobra publisher
  cobra_metrics_publish       Cobra metrics publisher
  cobra_to_statsd             Cobra to statsd
  cobra_to_cobra              Cobra to Cobra
  cobra_to_python             Cobra to python
  cobra_to_sentry             Cobra to sentry
  cobra_metrics_to_redis      Cobra metrics to redis
```

# Docker


## Build

```
$ env DOCKER_REPO=local make docker
```

## Run

```
$ docker run local/cobra_cli:2.9.100 --version
cobra_cli 2.9.100 ixwebsocket/11.0.4 linux ssl/mbedtls 2.16.3 zlib 1.2.11
```

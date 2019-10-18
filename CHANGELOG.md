# Changelog
All notable changes to this project will be documented in this file.

## [2.2.5] - 2019-10-17

* Bump sentry_sdk dependency

## [2.2.4] - 2019-10-17

* Fix performance problem when saving the last position received when subscribing (--resume_from_last_position)

## [2.2.3] - 2019-10-17

* Docker file second layer still reference an old Python. Default read/write subcommands channel clashes with the default publish/subcribe, so make it unique. Add --repeat option to write subcommand to indefinitely write.

## [2.2.2] - 2019-10-16

* Bump to python 3.8.0 proper. getVersion utility can take a module name.

## [2.2.1] - 2019-10-16

* Fix a memory leak in the client connection class

## [2.2.0] - 2019-10-15

* Add a --debug_memory_no_tracemalloc option to cobra run to have a 'slim' memory debugging mode.

## [2.1.9] - 2019-10-15

* bump tabulate to 0.8.5

## [2.1.8] - 2019-10-08

* bump sentry_sdk to 0.12.3

## [2.1.7] - 2019-10-02

* redis connections from the pipelined publishers are closed when terminating the app (mostly useful to get rid of python 3.8rc1 warnings when running the unittest)

## [2.1.6] - 2019-10-01

* display all http headers when catching zlib decompression error explicitly and logging an error

## [2.1.5] - 2019-10-01

* catch zlib decompression error explicitly and log an error including the connection id

## [2.1.4] - 2019-09-30

* sentry integration / report the user agent properly using the current sentry Hub (see https://github.com/getsentry/sentry-python/issues/483)

## [2.1.3] - 2019-09-30

* redis subscription: detect max number of clients reached error and fail rtm/subscribe commands

## [2.1.2] - 2019-09-27

* fix redis connection leak in rtm/delete

## [2.1.0] - 2019-09-25

* bump aio-redis dependency to 1.3.0

## [2.0.0] - 2019-09-19

* cobra works with python3.8 (beta4 at this point)

## [1.9.0] - 2019-09-18

* server / LIKE expression follows more closely the SQL standard, using globbing/fnmatch to evaluate expressions. LIKE can be used to compute startswith and endswith queries for strings. % (match all) and _ (match one) characters are supported, and mapped to * and ? fnmatch globbing special characters.

## [1.8.2] - 2019-09-17

* server / add a channel_max_length apps config parameter that limits how many messages can be retained in a single channel. Still default to a 1000 messages. The parameter is a global, top level yaml config for now. It is likely that we will make it a per appkey settings. In the example below we set it to 100. This parameter is helpful if you are trying to use cobra to transfer large messages.

```
$ head ~/.cobra.yaml
batch_publish_size: 50
channel_max_length: 100
```

## [1.8.1] - 2019-09-17

* server / user-agent recorded as a sentry context info is a python 3.7 Context Variable
* server / log a warning instead of an error when a connection is made with an invalid appkey

## [1.8.0] - 2019-09-17

* server / record user-agent as a sentry context info

## [1.7.9] - 2019-09-17

* server / log an error when a connection is made with an invalid appkey

## [1.7.8] - 2019-09-11

* server / return metadata about a stream (existence and length) when subscribing to a channel (in the body response)

## [1.7.7] - 2019-09-11

* bump sentry_sdk dep to 0.11.2

## [1.7.6] - 2019-09-11

* server / connection state holds a userAgent and has a __repr__ method, this should work with sentry errors to identify bad clients

## [1.7.5] - 2019-09-11

* server / connection id is 12 byte long, instead of 8. This might help with some rare collisions.

## [1.7.4] - 2019-09-10

* server / make disk logging work on Windows by using tempfile.gettempdir() instead of /tmp/

## [1.7.3] - 2019-09-09

* client / when closing a connection, make sure to unsubscribe all subscriptions

## [1.7.1] - 2019-08-29

### Changed

* bump click version

## [1.7.0] - 2019-08-28

### Changed

* rtm/delete delete a stream, instead of writing a null entry in it
* health check delete temp channel/streams + test read/write/delete

## [1.6.12] - 2019-08-28

### Changed

* Add optional http test in health-check, with --http_extra_check

## [1.6.11] - 2019-08-28

### Fixed

* Fixed a couple of pylint warnings
* Stop depending on ujson

## [1.6.10] - 2019-08-24

### Changed

* Upgrade uvloop dependency to 0.13.0 to hopefully solve [Fatal error on transport TCPTransport](https://github.com/MagicStack/uvloop/issues/244) kind of errors.
* Dockerfile uses Python 3.7.4

## [1.6.9] - 2019-08-23

### Fixed

Missing __init__.py file required to have a the handlers folder loaded.

## [1.6.8] - 2019-08-23

### Changed

- (client) New --summary option for cobra publish, usually used to see how many messages can be sent to a server per second

```
(venv) cobra$ cobra publish --url 'ws://jeanserge.com/v2?appkey=_health' --repeat --delay 0.001 --secret A5a3BdEfbc6Df5AAFFcadE7F9Dd7F17E --role health
Processing 1 items
1 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
19 per seconds
^C
Aborted!
```

## [1.6.7] - 2019-08-21

### Changed

- More unittest to test failures in pubsub and health-checks. Above 80% test coverage now.

```
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
cobras/__init__.py                          0      0   100%
cobras/client/__init__.py                   0      0   100%
cobras/client/client.py                    89     46    48%
cobras/client/connection.py               155     10    94%
cobras/client/credentials.py               12      0   100%
cobras/client/health_check.py              52     11    79%
cobras/client/monitor.py                  130     52    60%
cobras/client/publish.py                   14      0   100%
cobras/common/__init__.py                   0      0   100%
cobras/common/algorithm.py                  4      1    75%
cobras/common/apps_config.py              139     33    76%
cobras/common/auth_hash.py                  8      0   100%
cobras/common/cobra_types.py                3      0   100%
cobras/common/memoize.py                   11      0   100%
cobras/common/memory_debugger.py           70     10    86%
cobras/common/memory_usage.py              13      3    77%
cobras/common/task_cleanup.py              12      4    67%
cobras/common/throttle.py                  12      0   100%
cobras/common/version.py                    3      0   100%
cobras/server/__init__.py                   0      0   100%
cobras/server/app.py                      143     16    89%
cobras/server/connection_state.py          30      4    87%
cobras/server/handlers/admin.py            58     32    45%
cobras/server/handlers/auth.py             41     11    73%
cobras/server/handlers/kv_store.py         96     20    79%
cobras/server/handlers/pubsub.py          164     20    88%
cobras/server/pipelined_publisher.py       40     14    65%
cobras/server/pipelined_publishers.py      20      0   100%
cobras/server/protocol.py                  65     24    63%
cobras/server/redis_connections.py         24      0   100%
cobras/server/redis_subscriber.py          57      5    91%
cobras/server/stats.py                     97      8    92%
cobras/server/stream_sql.py               129     11    91%
-----------------------------------------------------------
TOTAL                                    1691    335    80%
```

## [1.6.6] - 2019-08-20

### Changed

- (server) upgrade sentry-sdk
- change pre-commit ordering
- cobra health failures are less noisy
- make sure the health-check fails when redis is down
- sort requirements file ...
- more pre-commit fun
- test client monitoring when redis is down
- (linter) fix indentation
- (doc) add note about some bad code
- (wip/disabled) unittest / add code to check how monitoring works when redis is down
- (server) when redis is down, and receiving a subscribe request, the server should send an error and it does not
- (client) handle and throw explicit exception when the server sends a message without an id
- read write test: add a test for when redis is down
- test_utils makeRunner can take a redis config as an optional arg
- remove unused parameter
- update makefile + README

## [1.6.5] - 2019-08-20

### Changed

- (server+client) key value store: add a delete operation
- (server) breaking protocol.py mega file into small ones

## [1.6.4] - 2019-08-20

### Changed

- (client) subscribe command: new --resume_from_last_position to start subscription where it was left of previously
- (server) write operations sets stream max length to be 1 entry only to keep that stream small

### Fixed

- format code with black + fix lint errors (flake8) / add linter to travis

## [1.6.3] - 2019-08-20

### Fixed

- (client) subscribe: when erroring while retrieving last position, the error message is lost

## [1.6.2] - 2019-08-20

### Fixed

- (client+server) read / write operations are handled gracefully when redis cannot be reached by the server

## [1.6.0] - 2019-08-19

### New feature

- (client) subscription can save and restore positions internally, so that no published events are missed in case a subscription trips up

### Fixed

- (client) in the connection class, remove queues used for events that have already been received from the server

## [1.5.3] - 2019-08-19

- (client) reconnect wait time can be parameterized, still default to 1 second

## [1.5.2] - 2019-08-18

- (client) New admin command argument handling. Run `cobra admin --help` to see available admin actions.
- (client) All command handle COBRA_PORT, so they will function properly in a docker environment, when hitting a local server with a non default port (!= 8765), through docker exec.
- (server) Add admin command to disconnect just one connection
- (server) Add admin command to retrieve all connection ids.

## [1.5.1] - 2019-08-18

### Changed

- cobras package is distributed as a wheel on PyPI. See [this](https://pythonwheels.com/).
- Unittest can be run in parallel with py.xdist. On a 2014 macbook the runtime goes from 15 seconds down to 7 seconds.

```
(venv) cobra$ py.test -n 10 tests
====================================== test session starts ======================================
platform darwin -- Python 3.7.2, pytest-5.0.1, py-1.8.0, pluggy-0.12.0
rootdir: /Users/bsergeant/src/foss/cobra
plugins: xdist-1.29.0, forked-1.0.2, cov-2.7.1
gw0 [37] / gw1 [37] / gw2 [37] / gw3 [37] / gw4 ok / gw5 [37] / gw6 ok / gw7 ok / gw8 [37] / gw9 gw0 [37] / gw1 [37] / gw2 [37] / gw3 [37] / gw4 [37] / gw5 [37] / gw6 ok / gw7 ok / gw8 [37] / gwgw0 [37] / gw1 [37] / gw2 [37] / gw3 [37] / gw4 [37] / gw5 [37] / gw6 [37] / gw7 ok / gw8 [37] / gw0 [37] / gw1 [37] / gw2 [37] / gw3 [37] / gw4 [37] / gw5 [37] / gw6 [37] / gw7 [37] / gw8 [37] gw0 [37] / gw1 [37] / gw2 [37] / gw3 [37] / gw4 [37] / gw5 [37] / gw6 [37] / gw7 [37] / gw8 [37] / gw9 [37]
.....................................                                                     [100%]
=================================== 37 passed in 7.06 seconds ===================================
(venv) cobra$ py.test
====================================== test session starts ======================================
platform darwin -- Python 3.7.2, pytest-5.0.1, py-1.8.0, pluggy-0.12.0
rootdir: /Users/bsergeant/src/foss/cobra
plugins: xdist-1.29.0, forked-1.0.2, cov-2.7.1
collected 37 items

tests/test_app.py ...                                                                     [  8%]
tests/test_apps_config.py ...                                                             [ 16%]
tests/test_client_publish.py .                                                            [ 18%]
tests/test_memory_debugger.py .                                                           [ 21%]
tests/test_merge_monitor_events.py .                                                      [ 24%]
tests/test_read_write.py .                                                                [ 27%]
tests/test_redis_connections.py ...                                                       [ 35%]
tests/test_redis_subscriber.py .                                                          [ 37%]
tests/test_stream_sql.py .....................                                            [ 94%]
tests/test_throttle.py .                                                                  [ 97%]
tests/test_validate_redis_position.py .                                                   [100%]

================================== 37 passed in 15.00 seconds ===================================```
```

## [1.5.0] - 2019-08-16
### Changed

- (bavarde cli) fix history

## [1.4.13] - 2019-08-16
### Changed

- (bavarde cli) add --verbose flag which works like the cobra flag.

## [1.4.12] - 2019-08-16
### Changed

- Catch and display readable error when failing to start the server. Classic case is running it twice in two terminals, binding to the same port.

```
2019-08-16 22:34:27 CRITICAL Cannot start cobra server: [Errno 48] error while attempting to bind on address ('127.0.0.1', 8765): address already in use
```

## [1.4.11] - 2019-08-16
### Changed

- --verbose (short -v) can be passed in to all cobra commands, and almost all printing goes through the logging library. Logging format is simplified by removing hostname and username.

```
2019-08-16 21:57:56 INFO < {'action': 'rtm/publish/ok', 'id': 2, 'body': {}}
```

## [1.4.10] - 2019-08-16
### Changed

- (bavarde client) when cancelling with Ctrl-C if a connection was not established yet, do not try to terminate it

## [1.4.6] - 2019-08-16
### Changed

- (server) when running inside docker with a non default port (COBRA_PORT), health check fails as it is trying to use the default port (8765). Modified healt check to look at COBRA_PORT environment variable

## [1.4.5] - 2019-08-16
### Changed

- fix unittest (kv read/write)

## [1.4.4] - 2019-08-16
### Changed

- (server) handle more exception types when failing to connect to redis (such as cannot resolve DNS name)

## [1.4.3] - 2019-08-16
### Changed

- (server) Handle invalid COBRA_APPS_CONFIG_CONTENT values

## [1.4.2] - 2019-08-16
### Changed

- health check return non 0 exit code when a problem happens, instead of retrying to connect and succeed

## [1.4.1] - 2019-08-16
### Changed

- client: fix hang when an exception is thrown (disconnection with the server for example) inside the coroutine waiting for server data

## [1.4.0] - 2019-08-16
### Changed

- Fix very unflexible design in the client code, where the client heavily expected server responses in a specific order. New design is more flexible, and concurrent subscriptions or multiple publish can happens at the same time.
- Server send a response to acknowledge publish messages.

## [1.3.4] - 2019-08-15

### Changed
- cobra can start if redis is down. Not being able to publish statistics is a non fatal error
- COBRA_APPS_CONFIG_CONTENT contains data that is gziped first before being encoded with base64. You can generate that blob with `gzip -c ~/.cobra.yaml | base64` on macOS, or `gzip -c ~/.cobra.yaml | openssl base64` if you have openssl installed ; you'll need to join all the blobs so that they are all on the same line in that case.

## [1.3.3] - 2019-08-15

### Changed
- cobra run can use an environment variable, COBRA_APPS_CONFIG_CONTENT, to specify the content of the configuration file

## [1.3.0] - 2019-08-15

### Changed
- Server has a simple key value store, internally storing data in stream (at the 'tip' of it). A value can be retrieved at a certain position.
- New `cobra read` and `cobra write` commands, to work with the Key Value Store

## [1.2.8] - 2019-08-14

### Changed
- `cobra publish` command broke because of refactoring
- use new exceptions types from websockets 8.0.2 to get better logging about connection termination

## [1.2.7] - 2019-08-13

### Changed
- update to websockets 8.0.2
- unittest does not run with warnings

## [1.2.6] - 2019-08-12

### Changed
- bavarde: colorize output
- client API changed, new connection class (wip)
- client subscriber API changed, takes a parsed json message + position

## [1.2.5] - 2019-08-12

### Changed
- bavarde client: first prompt line is not displayed with a regular prompt

## [1.2.4] - 2019-08-12

### Changed
- bavarde client: exiting with Ctrl-C cancel the subscription. Get rid of the message: `Task was destroyed but it is pending!`
- bavarde client: first prompt line is not displayed with a regular prompt

## [1.2.3] - 2019-08-10

### Changed
- bavarde client displays a time indication

```
[18:43:06] bsergeant> sdc
[18:43:06] bsergeant> adc
[18:45:17] bsergeant> dddddddddddd
```

## [1.2.2] - 2019-08-09

### Changed
- cobra server will reject invalid position when subscribing instead of ignoring it, which seems to trigger a hang when calling XREAD on a stream (needs to investigate)

## [1.2.0] - 2019-08-09

### Changed
- Add example code for a chat command line interactive client named bavarde. The chat connects to a public cobra server. Many features from a decent chat are missing, Most of the interactive chat code was taken from the websockets library.

## [1.1.1] - 2019-08-07

### Changed
- Use a more elegant way to retrieve cobras version number, with pkg_resources module.
- (health-check client) handle publish that triggers a server error (when redis is misconfigured)

## [1.1.0] - 2019-08-03

### Changed
- Implement permissions, to give certain roles publish or subscribe only permission. This can be used to add security and restrict a client in the wild to only publish its own data to a channel, but not to be able to look at traffic from different apps by subscribing on the same channel
- Improve error reporting in the health check command
- Make unsubscribing in the server code more robust, when passing in bogus data
- Add history support. Each published message has an id called a position. That id can be used when subscribing to retrieve messages that a subscriber would have missed if it was down while that message was published.
- Add read command (client + server) to retrieve one element from history. A write and a delete command are comming.
- Add --hide_roles, --hide_nodes and --system options to the monitor command, to deal with displaying info about cobra deployments with lots of nodes or roles. --system info does not display publish/subscribe statistics by nodes but instead system info such as connection count and numbers of asyncio tasks.

## [1.0.0] - 2019-07-31

### Changed
- Redis Streams instead of Redis PubSub are used internally to dispatch messages. History is not used at this point, so the change is really a pure swap without any added features, but we are ready for taking advantage of history.

## [0.0.196] - 2019-07-26
### Changed
- Initial release

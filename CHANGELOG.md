# Changelog
All notable changes to this project will be documented in this file.

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

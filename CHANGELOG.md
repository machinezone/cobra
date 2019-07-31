# Changelog
All notable changes to this project will be documented in this file.

## [1.0.0] - 2019-07-31
### Changed
- Redis Streams instead of Redis PubSub are used internally to dispatch messages. History is not used at this point, so the change is really a pure swap without any added features, but we are ready for taking advantage of history.

## [0.0.196] - 2019-07-26
### Changed
- Initial release

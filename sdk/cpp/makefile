#
# This makefile is used for convenience, and wrap simple cmake commands
# You don't need to use it as an end user, it is more for developer.
#
# * work with docker (linux build)
# * execute the unittest
#
# The default target will install cobra_cli
#
#
all: brew

install: brew

# installs all deps required for building the project
deps:
ifeq ($(shell uname),Darwin)
	sudo port install ninja
endif
	python3 -m pip install conan==1.33.0
	type conan && echo "done" || echo "\n\n\tcould not find 'conan'. Ensure python's bin/ directory is in your path\n\n"
	type conan

# Use -DCMAKE_INSTALL_PREFIX= to install into another location
# on osx it is good practice to make /usr/local user writable
# sudo chown -R `whoami`/staff /usr/local
#
# Release, Debug, MinSizeRel, RelWithDebInfo are the build types
#
# Default rule does not use python as that requires first time users to have Python3 installed
#
brew:
	mkdir -p build && (cd build ; conan install .. ; conan build .. ; cmake -GNinja -DCMAKE_BUILD_TYPE=MinSizeRel .. ; ninja install)

.PHONY: docker

NAME   := ${DOCKER_REPO}/cobra_cli
TAG    := $(shell sh tools/extract_version.sh)
IMG    := ${NAME}:${TAG}
LATEST := ${NAME}:latest
BUILD  := ${NAME}:build

print_version:
	@echo 'IXWebSocket version =>' ${TAG}

set_version:
	sh tools/update_version.sh ${VERSION}

docker_test:
	docker build -f docker/Dockerfile.debian -t bsergean/ixwebsocket_test:build .

docker:
	git clean -dfx
	docker build -t ${IMG} .
	docker tag ${IMG} ${BUILD}

docker_push:
	docker tag ${IMG} ${LATEST}
	docker push ${LATEST}
	docker push ${IMG}

# this is helpful to remove trailing whitespaces
trail:
	sh third_party/remote_trailing_whitespaces.sh

format:
	clang-format -i `find test ixwebsocket ws -name '*.cpp' -o -name '*.h'`

change: format
	vim ixcobra/ixcobra/IXCobraVersion.h docs/CHANGELOG.md

change_no_format:
	vim ixcobra/ixcobra/IXCobraVersion.h docs/CHANGELOG.md

commit:
	git commit -am "`sh tools/extract_latest_change.sh`"

.PHONY: test
.PHONY: build
.PHONY: ws

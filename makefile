# Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

all: flake

install-python:
	@echo "--> Installing Python dependencies"
	# order matters here, base package must install first
	cp requirements.txt /tmp/
	pip install -U pip
	pip install --requirement /tmp/requirements.txt
	pip install -e .
	pip install "file://`pwd`#egg=cobras[dev]"

install-python-tests:
	pip install "file://`pwd`#egg=cobras[dev,tests]"

develop-only: install-python install-python-tests 

dev: develop
develop: develop-only install-python-tests

upload:
	rm dist/*
	python setup.py sdist
	twine upload dist/*

lint: flake

flake:
	flake8 `find src -name '*.py'`

test:
	py.test --disable-warnings tests/*.py

test_server:
	./venv/bin/py.test tests/test_app.py::test_server
	# ./venv/bin/py.test tests/test_app.py::test_server_mem

mypy:
	mypy --ignore-missing-imports src/cobras/server/*.py src/cobras/common/*.py


coverage:
	py.test --disable-warnings --cov=cobras.server --cov=cobras.common --cov-report html --cov-report term tests

isort:
	isort `find src tests -name '*.py'`

# this is helpful to remove trailing whitespaces
trail:
	test `uname` = Linux || sed -E -i '' -e 's/[[:space:]]*$$//' `find src tests -name '*.py'`
	test `uname` = Darwin || sed -i 's/[ \t]*$$//' `find src tests -name '*.py'`

clean:
	find src tests -name '*.pyc' -delete
	rm -f *.pyc

#
# Docker
#
NAME   := ${DOCKER_REPO}/cobra
TAG    := $(shell cat DOCKER_VERSION)
IMG    := ${NAME}:${TAG}
BUILD  := ${NAME}:build
PROD   := ${NAME}:production

bump:
	python tools/bump_docker_version.py

docker_tag: bump
	docker tag ${IMG} ${PROD}
	docker push ${PROD}
	oc import-image -n cobra-live cobra:production
	oc import-image -n cobra-internal cobra:production

docker:
	docker build -t ${IMG} .
	docker tag ${IMG} ${BUILD}
	docker tag ${IMG} ${PROD}

docker_push: docker_tag

dummy: docker

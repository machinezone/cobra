# Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

all: pylint

dev:
	@echo "--> Installing Python dependencies"
	# order matters here, base package must install first
	pip install -U pip
	pip install --requirement requirements.txt
	pip install --requirement tests/requirements.txt
	pip install -e .
	pip install "file://`pwd`#egg=cobras[dev]"

upload:
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload dist/*.whl
	rm -rf build/

lint: flake

indent:
	black -S cobras tests

format: indent

flake:
	flake8 --max-line-length=88 `find cobras -name '*.py'`

test:
	py.test -n 4 --disable-warnings tests/*.py

test_server:
	./venv/bin/py.test --disable-warnings tests/test_app.py::test_server
	# ./venv/bin/py.test tests/test_app.py::test_server_mem

mypy:
	mypy --ignore-missing-imports cobras/server/*.py cobras/common/*.py

pylint:
	pylint -E -j 10 -r n -d C0301 -d C0103 -d C0111 -d C0330 -d W1401 -d W1203 -d W1202 `find cobras -name '*.py'`

coverage:
	py.test -n 4 --disable-warnings --cov=cobras --cov-report html --cov-report term tests

isort:
	isort `find cobras tests -name '*.py'`

# this is helpful to remove trailing whitespaces
trail:
	test `uname` = Linux || sed -E -i '' -e 's/[[:space:]]*$$//' `find src tests -name '*.py'`
	test `uname` = Darwin || sed -i 's/[ \t]*$$//' `find src tests -name '*.py'`

#  python -m venv venv
#  source venv/bin/activate
#  pip install mkdocs
doc:
	mkdocs gh-deploy

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

docker_tag:
	docker tag ${IMG} ${PROD}
	docker push ${PROD}
	docker push ${IMG}
	oc import-image -n cobra-live cobra:production
	oc import-image -n cobra-internal cobra:production

docker:
	git clean -dfx -e venv -e cobras.egg-info/
	docker build -t ${IMG} .
	docker tag ${IMG} ${BUILD}
	docker tag ${IMG} ${PROD}

docker_push: docker_tag

deploy: docker docker_push

dummy: docker

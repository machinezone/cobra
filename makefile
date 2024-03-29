# Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.

all: pylint

update_version:
	python tools/compute_version_from_git.py > DOCKER_VERSION

dev: update_version
	@echo "--> Installing Python dependencies"
	# order matters here, base package must install first
	pip install -U pip
	# pip install git+https://github.com/bsergean/aredis.git@6668469#egg=aredis
	pip install --requirement requirements.txt
	pip install --requirement tests/requirements.txt
	pip install -e .
	pip install "file://`pwd`#egg=cobras[dev]"
	pip install pre-commit
	pre-commit install

release:
	git push ; make upload

upload: update_version
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
	echo "Make sure redis is running before starting tests!...\n\n\n"
	py.test -n 4 --disable-warnings tests/*.py

test_server:
	echo "Make sure redis is running before starting tests!...\n\n\n"
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
TAG    := $(shell python tools/compute_version_from_git.py)
IMG    := ${NAME}:${TAG}
BUILD  := ${NAME}:build
PROD   := ${NAME}:production
STAGE  := ${NAME}:staging

bump:
	python tools/bump_docker_version.py

push_prod:
	docker tag ${IMG} ${PROD}
	docker push ${IMG}
	docker push ${PROD}

push_stage:
	docker tag ${IMG} ${STAGE}
	docker push ${IMG}
	docker push ${STAGE}

docker: update_version
	git clean -dfx -e venv -e cobras.egg-info/ -e DOCKER_VERSION
	docker build -t ${IMG} .
	docker tag ${IMG} ${BUILD}
	docker tag ${IMG} ${STAGE}

docker_bavarde:
	git clean -dfx -e venv -e cobras.egg-info/
	docker build -f cobras/bavarde/Dockerfile -t ${IMG} .
	docker tag ${IMG} ${BUILD}
	docker tag ${IMG} ${PROD}

docker_bavarde_push:
	docker tag ${IMG} ${PROD}
	docker push ${PROD}
	docker push ${IMG}

docker_push: docker_tag

deploy: docker docker_push

dummy: docker

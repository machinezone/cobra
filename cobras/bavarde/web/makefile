all: deps_installed
	mkdir -p build
	./node_modules/.bin/webpack -w

deps_installed: package.json
	npm i && touch deps_installed

bundle:
	mkdir -p build
	cp conf/live.js src/default_conf.js
	./node_modules/.bin/webpack

install: bundle

bump_version:
	python tools/bump.py

bump: bump_version
	git tag v`cat VERSION`
	git add VERSION
	git commit -m "bump version number -> `cat VERSION`" VERSION

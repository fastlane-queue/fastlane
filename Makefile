COMPOSE := $(shell command -v docker-compose 2> /dev/null)
POETRY := $(shell command -v poetry 2> /dev/null)
LAST_TAG := $(shell git for-each-ref --format='%(*committerdate:raw)%(committerdate:raw) %(refname) %(*objectname) %(objectname)' refs/tags 2>/dev/null | sort -n | awk '{ print $$3 }' | tail -n1 | sed s@refs/tags/@@g)

setup:
ifndef POETRY
	@echo "You must have poetry installed (https://github.com/sdispater/poetry)."
	@echo
	@exit 1
endif
	@poetry install

setup-ci:
	@pip install poetry
	@poetry develop

deps:
	@mkdir -p /tmp/fastlane/{mongo,redis,redis2,redis-sentinel}
ifdef COMPOSE
	@echo "Starting dependencies..."
	@docker-compose --project-name fastlane up -d
	@echo "Dependencies started successfully."
endif
	@-docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock

deps-build:
ifdef COMPOSE
	@echo "Starting dependencies..."
	@docker-compose --project-name fastlane up --build -d
	@echo "Dependencies started successfully."
endif
	@-docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock

stop-deps:
ifdef COMPOSE
	@echo "Stopping dependencies..."
	@docker-compose --project-name fastlane stop
	@docker-compose --project-name fastlane rm -f
endif

docker-build:
	@docker build -t fastlane .

docker-push: docker-build
	@docker tag fastlane heynemann/fastlane:${LAST_TAG}
	@docker push heynemann/fastlane:${LAST_TAG}
	@docker tag fastlane heynemann/fastlane:latest
	@docker push heynemann/fastlane:latest

test:
	@poetry run pytest -sv --quiet --nf --cov=fastlane tests/

focus:
	@poetry run pytest -sv --quiet --nf -m focus --cov=fastlane tests/

watch:
	@poetry run ptw -c -w -- --quiet --nf --cov=fastlane tests/

run:
	@fastlane api -vvv -c ./fastlane/config/local.conf

worker:
	@#This env must be set in MacOS to ensure that docker py works
	@OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES fastlane worker -vv -c ./fastlane/config/local.conf

publish: docker-push
	@poetry build
	@poetry publish

coverage:
	@coverage html
	@open htmlcov/index.html

sample:
	@mkdir -p /tmp/fastlane/{mongo,redis}
ifdef COMPOSE
	@echo "Starting fastlane..."
	@docker-compose -f ./docker-compose-sample.yml --project-name fastlane up -d
	@echo "fastlane started successfully."
endif

COMPOSE := $(shell command -v docker-compose 2> /dev/null)
YARN := $(shell command -v yarn 2> /dev/null)
POETRY := $(shell command -v poetry 2> /dev/null)
LAST_TAG := $(shell git for-each-ref --format='%(*committerdate:raw)%(committerdate:raw) %(refname) %(*objectname) %(objectname)' refs/tags 2>/dev/null | sort -n | awk '{ print $$3 }' | tail -n1 | sed s@refs/tags/@@g)
OS_NAME := $(shell uname -s)

.PHONY: docs

setup:
ifndef POETRY
	@echo "You must have poetry installed (https://github.com/sdispater/poetry)."
	@echo
	@exit 1
endif
	@poetry install
ifdef YARN
	@yarn install
else
	@npm install
endif

setup-ci:
	@pip install poetry
	@poetry develop

check-sec:
ifdef COMPOSE
	@echo "Installing Bandit..."
	@pip install bandit
	@echo "Running Bandit..."
	@bandit -r .
endif

deps:
ifdef COMPOSE
	@echo "Starting dependencies..."
	@docker-compose --project-name fastlane up -d
	@echo "Dependencies started successfully."
endif

deps-build:
ifdef COMPOSE
	@echo "Starting dependencies..."
	@docker-compose --project-name fastlane up --build -d
	@echo "Dependencies started successfully."
endif

stop-deps:
ifdef COMPOSE
	@echo "Stopping dependencies..."
	@docker-compose --project-name fastlane down -v --remove-orphans
	@docker-compose --project-name fastlane rm --stop --force
endif

stop-deps-func:
ifdef COMPOSE
	@echo "Stopping func tests dependencies..."
	@docker-compose --project-name fastlane-tests -f ./docker-compose-func-tests.yml down -v
endif

deps-func: stop-deps stop-deps-func
ifdef COMPOSE
	@echo "Starting func tests dependencies..."
	@docker-compose --project-name fastlane-tests -f ./docker-compose-func-tests.yml up -d
	@echo "Func tests dependencies started successfully."
endif

docker-build:
	@docker build -t fastlane .

docker-push: docker-build
	@docker tag fastlane heynemann/fastlane:${LAST_TAG}
	@docker push heynemann/fastlane:${LAST_TAG}
	@docker tag fastlane heynemann/fastlane:latest
	@docker push heynemann/fastlane:latest

test: deps unit deps-func func

unit:
	@poetry run pytest -sv --quiet --nf --cov=fastlane tests/unit/

focus:
	@poetry run pytest -sv --quiet --nf -m focus --cov=fastlane tests/unit/

watch:
	@poetry run ptw -c -w -- --quiet --nf --cov=fastlane tests/unit/

func:
	@poetry run pytest -s --quiet --nf tests/func/

run: deps
	@poetry run fastlane api -vvv -c ./fastlane/config/local.conf

worker:
	@#This env must be set in MacOS to ensure that docker py works
	@OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES fastlane worker -vv -c ./fastlane/config/local.conf

publish: docker-push
	@poetry build
	@poetry publish

coverage:
	@coverage html
ifeq ($(OS_NAME),Linux)
	@firefox `pwd`/htmlcov/index.html
else
	@open htmlcov/index.html
endif

sample:
ifdef COMPOSE
	@echo "Starting fastlane..."
	@docker-compose -f ./docker-compose-sample.yml --project-name fastlane-sample up -d
	@echo "fastlane started successfully."
endif

readme:
	#ensure remark is installed with
	#npm install --global remark-cli remark-preset-lint-recommended remark-stringify
	@remark README.md -o README.md

lint:
	@pylint fastlane
	@flake8

docs:
	@mkdocs build && open site/index.html

update-config-doc:
	@echo '## Configuration Options' > docs/configuration.md
	@echo '' >> docs/configuration.md
	@echo 'To generate a sample configuration file like this one: `fastlane config\.' >> docs/configuration.md
	@echo '' >> docs/configuration.md
	@echo '```python' >> docs/configuration.md
	@poetry run fastlane config >> docs/configuration.md
	@echo '```' >> docs/configuration.md
	@sed -i.bak 's/^#//g' docs/configuration.md
	@rm docs/configuration.md.bak


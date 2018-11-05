COMPOSE := $(shell command -v docker-compose 2> /dev/null)
POETRY := $(shell command -v poetry 2> /dev/null)

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
ifdef COMPOSE
	@echo "Starting dependencies..."
	@docker-compose --project-name easyq up -d
	@echo "Dependencies started successfully."
endif
	@docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock

stop-deps:
ifdef COMPOSE
	@echo "Stopping dependencies..."
	@docker-compose --project-name easyq stop
	@docker-compose --project-name easyq rm -f
endif

test:
	@poetry run pytest -sv --quiet --nf --cov=easyq tests/

focus:
	@poetry run pytest -sv --quiet --nf -m focus --cov=easyq tests/

watch:
	@poetry run ptw -c -w -- --quiet --nf --cov=easyq tests/

run:
	@easyq api -vvv

worker:
	@#This env must be set in MacOS to ensure that docker py works
	@OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES easyq worker -vv

coverage:
	@coverage html
	@open htmlcov/index.html

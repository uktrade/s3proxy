SHELL := /bin/bash
APPLICATION_NAME="S3PROXY"

# Colour coding for output
COLOUR_NONE=\033[0m
COLOUR_GREEN=\033[32;01m
COLOUR_YELLOW=\033[33;01m
COLOUR_RED='\033[0;31m'

.PHONY: help test
help:
	@echo -e "$(COLOUR_GREEN)|--- $(APPLICATION_NAME) ---|$(COLOUR_NONE)"
	@echo -e "$(COLOUR_YELLOW)make build$(COLOUR_NONE) : Run docker-compose build"
	@echo -e "$(COLOUR_YELLOW)make up$(COLOUR_NONE) : Run docker-compose up"
	@echo -e "$(COLOUR_YELLOW)make reload$(COLOUR_NONE) : Run docker-compose restart s3proxy"
	@echo -e "$(COLOUR_YELLOW)make rebuild$(COLOUR_NONE) : Run docker-compose up --detach --build"
	@echo -e "$(COLOUR_YELLOW)make up-detached$(COLOUR_NONE) : Run docker-compose up in detached mode (useful for CI)"
	@echo -e "$(COLOUR_YELLOW)make down$(COLOUR_NONE) : Run docker-compose down"
	@echo -e "$(COLOUR_YELLOW)make bash$(COLOUR_NONE) : Start a bash session on a new application container"
	@echo -e "$(COLOUR_YELLOW)make shell$(COLOUR_NONE) : Start a bash session on the running application container if it exists"
	@echo -e "$(COLOUR_YELLOW)make format$(COLOUR_NONE) : Run black and isort"
	@echo -e "$(COLOUR_YELLOW)make test$(COLOUR_NONE) : Run tests - can pass argument to specify a single test with make test test=<name_of_your_test>"
	@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Run flake8 checks"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black"
	@echo -e "$(COLOUR_YELLOW)make isort$(COLOUR_NONE) : Run isort"
	@echo -e "$(COLOUR_YELLOW)make mypy$(COLOUR_NONE) : Run mypy"
	@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate pip requirements files"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-init$(COLOUR_NONE) : Initialise the detect-secrets for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-scan$(COLOUR_NONE) : detect-secrets scan for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-audit$(COLOUR_NONE) : detect-secrets audit for the project"
	@echo -e "$(COLOUR_YELLOW)make pre-commit$(COLOUR_NONE) : manually run pre-commit hook config against all files"

compose-ci = docker compose -f docker-compose.yml -f docker-compose.test.yml
compose-dev = docker compose -f docker-compose.yml -f docker-compose.test.yml -f docker-compose.dev.yml

build:
	$(compose-dev) build

up: down
	$(compose-dev) up

reload:
	$(compose-dev) restart main

rebuild:
	$(compose-dev) up --detach --build

up-detached:
	$(compose-dev) up -d

down:
	docker-compose down

run = $(compose-dev) run --rm
poetry = $(run) main poetry --quiet

run-ci =$(compose-ci) exec -it
poetry-ci = $(run-ci) main poetry

flake8:
	$(poetry) run flake8 $(file)

black:
	$(poetry) run black .

isort:
	$(poetry) run isort .

format: black isort

mypy:
	$(poetry) run mypy .

bash:
	$(run) -v ./:/app/ main bash

shell:
	docker-compose exec main bash

all-requirements:
	$(poetry) export -f requirements.txt --output requirements.txt --without-hashes --without dev,testing

# internal use to allow `test` command to have other dependencies
runtests:
	$(poetry-ci) run python -m unittest -v -b $(test)

test: down up runtests down

view-coverage:
	@echo -e "$(COLOUR_RED)@TODO!$(COLOUR_NONE)"
#	python -m webbrowser -t htmlcov/index.html

detect-secrets-init:
	$(poetry) run detect-secrets scan > .secrets.baseline

detect-secrets-scan:
	$(poetry) run detect-secrets scan --baseline .secrets.baseline

detect-secrets-audit:
	$(poetry) run detect-secrets audit .secrets.baseline

poetry-update:
	$(poetry) update

check-fixme:
	! git --no-pager grep -rni fixme -- ':!./makefile' ':!./.circleci/config.yml' ':!./.github/workflows/test.yml'
	! git --no-pager grep -rni @TODO -- ':!./makefile'

pre-commit:
	$(poetry) run pre-commit run --all-files

lint-ci:
	$(poetry-ci) run black .
	$(poetry-ci) run isort .
	$(poetry-ci) run flake8 $(file)
	$(poetry-ci) run mypy .
	! git --no-pager grep -rni fixme -- ':!./makefile' ':!./.circleci/config.yml' ':!./.github/workflows/test.yml'
	! git --no-pager grep -rni @TODO -- ':!./makefile'

test-ci:
	make runtests

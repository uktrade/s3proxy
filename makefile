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
	@echo -e "$(COLOUR_YELLOW)make up-detached$(COLOUR_NONE) : Run docker-compose up in detached mode"
	@echo -e "$(COLOUR_YELLOW)make down$(COLOUR_NONE) : Run docker-compose down"
	@echo -e "$(COLOUR_YELLOW)make bash$(COLOUR_NONE) : Start a bash session on the application container"
	@echo -e "$(COLOUR_YELLOW)make format$(COLOUR_NONE) : Run black and isort"
	@echo -e "$(COLOUR_YELLOW)make test$(COLOUR_NONE) : Run tests"
	@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Run flake8 checks"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black"
	@echo -e "$(COLOUR_YELLOW)make isort$(COLOUR_NONE) : Run isort"
	@echo -e "$(COLOUR_YELLOW)make mypy$(COLOUR_NONE) : Run mypy"
	@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate pip requirements files"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-init$(COLOUR_NONE) : Initialise the detect-secrets for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-scan$(COLOUR_NONE) : detect-secrets scan for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-audit$(COLOUR_NONE) : detect-secrets audit for the project"

build:
	docker-compose build

up:
	docker-compose up

up-detached:
	docker-compose up -d

down:
	docker-compose down

run = docker-compose run --rm
poetry = $(run) s3proxy poetry --quiet

flake8:
#	$(poetry) run flake8 $(file)
    @echo -e "$(COLOUR_RED)|--- @TODO! ---|$(COLOUR_NONE)"

black:
	$(poetry) run black .

isort:
#	$(poetry) run isort .
    @echo -e "$(COLOUR_RED)|--- @TODO! ---|$(COLOUR_NONE)"

format: black isort

mypy:
	$(poetry) run mypy .

bash:
	$(run) s3proxy bash

all-requirements:
	$(poetry) export -f requirements.txt --output requirements.txt --without-hashes --with production --without dev,testing

#pytest:
#	$(run) s3proxy pytest --cov --cov-report html -raP --capture=sys -n 4

test:
#	$(run) s3proxy pytest --disable-warnings --reuse-db $(test)
    @echo -e "$(COLOUR_RED)|--- @TODO! ---|$(COLOUR_NONE)"

#test-fresh:
#	$(run) s3proxy pytest --disable-warnings --create-db --reuse-db $(test)

#view-coverage:
#	python -m webbrowser -t htmlcov/index.html

detect-secrets-init:
	$(poetry) run detect-secrets scan > .secrets.baseline

detect-secrets-scan:
	$(poetry) run detect-secrets scan --baseline .secrets.baseline

detect-secrets-audit:
	$(poetry) run detect-secrets audit .secrets.baseline

poetry-update:
	$(poetry) update
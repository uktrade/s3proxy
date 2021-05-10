SHELL := /bin/bash
APPLICATION_NAME="S3 Proxy"

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
	@echo -e "$(COLOUR_YELLOW)make down$(COLOUR_NONE) : Run docker-compose down"
	@echo -e "$(COLOUR_YELLOW)make bash$(COLOUR_NONE) : Start a bash session on the application container"
	@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Run flake8 checks"
	@echo -e "$(COLOUR_YELLOW)make requirements$(COLOUR_NONE) : Run pip-compile and generate requirements files"
	@echo -e "$(COLOUR_YELLOW)make makemigrations$(COLOUR_NONE) : Run Django makemigrations"
	@echo -e "$(COLOUR_YELLOW)make migrations$(COLOUR_NONE) : Run Django makemigrations"
	@echo -e "$(COLOUR_YELLOW)make migrate$(COLOUR_NONE) : Run Django migrate"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black formatter"

build:
	docker-compose build

up:
	docker-compose up

down:
	docker-compose down

bash:
	docker-compose run --rm s3proxy bash

flake8:
	docker-compose run --rm s3proxy flake8 $(file)

all-requirements:
	docker-compose run --rm s3proxy pip-compile --output-file requirements/base.txt requirements.in/base.in
	docker-compose run --rm s3proxy pip-compile --output-file requirements/dev.txt requirements.in/dev.in
	docker-compose run --rm s3proxy pip-compile --output-file requirements/prod.txt requirements.in/prod.in

makemigrations:
	docker-compose run --rm s3proxy python manage.py makemigrations

migrations:
	docker-compose run --rm s3proxy python manage.py makemigrations

migrate:
	docker-compose run --rm s3proxy python manage.py migrate

black:
	docker-compose run --rm s3proxy black .

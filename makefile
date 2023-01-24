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
	@echo -e "$(COLOUR_YELLOW)make down$(COLOUR_NONE) : Run docker-compose down"
	@echo -e "$(COLOUR_YELLOW)make migrations$(COLOUR_NONE) : Run Django makemigrations"
	@echo -e "$(COLOUR_YELLOW)make migrate$(COLOUR_NONE) : Run Django migrate"
	@echo -e "$(COLOUR_YELLOW)make compilescss$(COLOUR_NONE) : Compile SCSS into CSS"
	@echo -e "$(COLOUR_YELLOW)make shell$(COLOUR_NONE) : Run a Django shell"
	@echo -e "$(COLOUR_YELLOW)make flake8$(COLOUR_NONE) : Run flake8 checks"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black"
	@echo -e "$(COLOUR_YELLOW)make isort$(COLOUR_NONE) : Run isort"
	@echo -e "$(COLOUR_YELLOW)make collectstatic$(COLOUR_NONE) : Run Django BDD tests"
	@echo -e "$(COLOUR_YELLOW)make bash$(COLOUR_NONE) : Start a bash session on the application container"
	@echo -e "$(COLOUR_YELLOW)make all-requirements$(COLOUR_NONE) : Generate pip requirements files"
	@echo -e "$(COLOUR_YELLOW)make pytest$(COLOUR_NONE) : Run pytest"
	@echo -e "$(COLOUR_YELLOW)make black$(COLOUR_NONE) : Run black formatter"
	@echo -e "$(COLOUR_YELLOW)make serve-docs$(COLOUR_NONE) : Serve mkdocs on port 8002"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-init$(COLOUR_NONE) : Initialise the detect-secrets for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-scan$(COLOUR_NONE) : detect-secrets scan for the project"
	@echo -e "$(COLOUR_YELLOW)make detect-secrets-audit$(COLOUR_NONE) : detect-secrets audit for the project"

build:
	docker-compose build

utils-build:
	docker-compose -f docker-compose.yml -f docker-compose.utils.yml build utils

up:
	docker-compose up

up-detached:
	docker-compose up -d

down:
	docker-compose down

run = docker-compose run --rm
manage = python manage.py
poetry = $(run) leavers poetry --quiet

first-use:
	docker-compose down
	docker-compose up -d db opensearch
	$(run) leavers python manage.py createcachetable
	$(run) leavers python manage.py migrate
	$(run) leavers python manage.py initialise_staff_index
	$(run) leavers python manage.py create_test_users
	$(run) leavers python manage.py seed_employee_ids
	$(run) leavers python manage.py update_staff_index
	$(run) leavers python manage.py set_permissions
	$(run) leavers python manage.py create_test_users
	docker-compose up

check-fixme:
	! git --no-pager grep -rni fixme -- ':!./makefile' ':!./.circleci/config.yml'

migrations:
	$(run) leavers python manage.py makemigrations

empty-migration:
	$(run) leavers python manage.py makemigrations $(app) --empty --name=$(name)

migrate:
	$(run) leavers python manage.py migrate

checkmigrations:
	$(run) --no-deps leavers python manage.py makemigrations --check

compilescss:
	npm run build

shell:
	$(run) leavers python manage.py shell

utils-shell:
	docker-compose -f docker-compose.yml -f docker-compose.utils.yml run --rm utils /bin/bash

flake8:
	$(run) leavers flake8 $(file)

black:
	$(run) leavers black .

isort:
	$(run) leavers isort .

format: black isort

mypy:
	$(run) leavers mypy .

collectstatic:
	$(run) leavers python manage.py collectstatic

bash:
	$(run) leavers bash

all-requirements:
	$(poetry) export -f requirements.txt --output requirements.txt --without-hashes --with production --without dev,testing

pytest:
	$(run) leavers pytest --cov --cov-report html -raP --capture=sys -n 4

test:
	$(run) leavers pytest --disable-warnings --reuse-db $(test)

test-fresh:
	$(run) leavers pytest --disable-warnings --create-db --reuse-db $(test)

view-coverage:
	python -m webbrowser -t htmlcov/index.html

superuser:
	$(run) leavers python manage.py createsuperuser

test-users:
	$(run) leavers python manage.py create_test_users

seed-employee-ids:
	$(run) leavers python manage.py seed_employee_ids

model-graphs:
	$(run) leavers python manage.py graph_models -a -g -o jml_data_model.png

ingest-activity-stream:
	$(run) leavers python manage.py ingest_activity_stream --limit=10

serve-docs:
	docker-compose up docs

staff-index:
	$(run) leavers $(manage) ingest_staff_data --skip-ingest-staff-records --skip-service-now

detect-secrets-init:
	$(poetry) run detect-secrets scan > .secrets.baseline

detect-secrets-scan:
	$(poetry) run detect-secrets scan --baseline .secrets.baseline

detect-secrets-audit:
	$(poetry) run detect-secrets audit --baseline .secrets.baseline

poetry-update:
	$(poetry) update

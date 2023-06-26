# Heavily inspired by / copied from https://github.com/tj-django/django-clone/blob/main/Makefile (thank you)
# Self-Documented Makefile see https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html

.DEFAULT_GOAL := help

# Put it first so that "make" without argument is like "make help".
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-32s-\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: help

# --------------------------------------------------------
# ------- Commands ---------------------------------------
# --------------------------------------------------------

ARCH?=amd64
docker_arch: ## set the arch environment variable for docker
	@export ARCH=$(ARCH)

docker_up: docker_arch ## runs docker compose up and waits for postgres to be ready
	docker-compose -f local.yml up -d django
	docker-compose -f local.yml exec django /entrypoint

coverage:  ## runs pytest and outputs coverage to coverage.xml
	pytest --cov imperium --cov-report xml

clean: clean-test clean-build clean-pyc  ## remove all build, test, coverage and Python artifacts

clean-test:  ## remove test and coverage artifacts
	rm -rf .tox/
	rm -f .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache

clean-build:  ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:  ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

dist: clean  ## builds source and wheel package
	python3 -m pip install --upgrade pip
	python3 -m pip install --upgrade build twine
	python3 -m build

# Note .pypirc is an untracked file containing secrets for auth with pypi.org
# todo when tests exist add coverage to dependencies here as well as dist
# todo consider automating commit, tag and push?
release: dist  ## package and upload a release, to make a new release first update the version number in setup.cfg
	twine upload --config-file .pypirc dist/*
	@echo "Package published to pypi! Now commit changes and push."

backupdb: docker_up ## Backup the db to postgres_backups dir
	docker-compose -f local.yml exec postgres backup

FILENAME?=$(shell ls -at postgres_backups/*.sql.gz | head -n1 | xargs basename)
restoredb: docker_up ## Restore the latest backup or defined FILENAME in postgres_backups
	docker-compose -f local.yml stop django
	docker-compose -f local.yml exec postgres restore $(FILENAME)
	docker-compose -f local.yml start django

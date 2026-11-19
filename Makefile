.PHONY: clean clean-test clean-pyc clean-build help test integration-test runserver runserver-reset
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
        match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
        if match:
                target, help = match.groups()
                print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

# The tests and the dev server run in containers (docker/compose.yml), against MariaDB as deployed;
# the host needs only Docker with Compose. Each use is its own Compose project.
COMPOSE := docker compose -f docker/compose.yml

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with flake8
	flake8 .


nopyc: clean-pyc
	find . -name "*.pyc" -exec rm -vf {} \;

test: ## run the Django tests in a container, against a fresh MariaDB (docker/compose.yml)
	$(COMPOSE) -p appstore-test run --rm --build tests; status=$$?; \
	$(COMPOSE) -p appstore-test down -v --remove-orphans; exit $$status

integration-test: ## run the Playwright integration suite (Chromium, Firefox) in containers against the App Store on MariaDB
	sh docker/integration-test.sh

runserver: ## run the App Store on http://127.0.0.1:8000, on a MariaDB kept across restarts
	$(COMPOSE) -p appstore-dev up --build serve

runserver-reset: ## remove make runserver's database and generated migrations
	$(COMPOSE) -p appstore-dev down -v --remove-orphans

.PHONY: clean clean-test clean-pyc clean-build help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
        from urllib import pathname2url
except:
        from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
        match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
        if match:
                target, help = match.groups()
                print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

# project virtualenv, managed with uv (host prerequisite, like the python runtime)
VENV := .venv
PYTHON := $(VENV)/bin/python
# written only after every setup step succeeds, so a failed setup is retried by the next make
VENV_STAMP := $(VENV)/.installed

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

test: build ## run tests via python manage.py test
	$(PYTHON) manage.py test

coverage: build ## check code coverage
	coverage run --source '.' --omit=*/tests.py,*/migrations/*,build/*,wsgi.py manage.py test
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

$(VENV_STAMP): requirements.txt requirements-test.txt ## create the virtualenv with uv and install requirements
	uv venv --allow-existing --python 3.12 $(VENV)
	uv pip install --python $(PYTHON) -r requirements.txt -r requirements-test.txt
	$(PYTHON) -m playwright install chromium
	touch $(VENV_STAMP)

build: $(VENV_STAMP) ## Build app database and static content in build directory
	mkdir -p build/whoosh_index
	mkdir -p build/media
	# should fix errors upon calling python manage.py commands
	-uv pip uninstall --python $(PYTHON) python-openid
	-uv pip uninstall --python $(PYTHON) python3-openid
	uv pip install --python $(PYTHON) python3-openid
	$(PYTHON) manage.py makemigrations apps --noinput
	$(PYTHON) manage.py makemigrations backend --noinput
	$(PYTHON) manage.py makemigrations download --noinput
	$(PYTHON) manage.py makemigrations help --noinput
	$(PYTHON) manage.py makemigrations search --noinput
	$(PYTHON) manage.py makemigrations submit_app --noinput
	$(PYTHON) manage.py makemigrations users --noinput
	$(PYTHON) manage.py makemigrations --noinput
	$(PYTHON) manage.py migrate --noinput
	$(PYTHON) manage.py rebuild_index --noinput


runserver: build ## Runs server locally
	$(PYTHON) manage.py runserver

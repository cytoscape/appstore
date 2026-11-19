# The App Store's images for docker/compose.yml, which make test, make integration-test and
# make runserver use: Django's dev server with DEBUG on, against MariaDB as deployed.
#   app:  the App Store (the integration suite's target, and make runserver)
#   test: the App Store with the test requirements and Chromium (make test)
FROM python:3.12.7-slim-bookworm AS base

COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv \
    DJANGO_SETTINGS_MODULE=settings.container

# the MySQL client library and headers, to build mysqlclient; and unzip, which extracting a
# release's Javadocs runs (apps/models.py), as bootstrap.sh installs it on the servers
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-libmysqlclient-dev pkg-config build-essential unzip \
    && rm -rf /var/lib/apt/lists/*

# ROOT_URLCONF is 'appstore.urls', so the code must live in a directory named appstore
WORKDIR /srv/appstore

COPY requirements.txt .
# mysqlclient is the driver prod uses, which installs it from conda rather than requirements.txt;
# then the python-openid swap the Makefile's build target made
RUN uv pip install --system -r requirements.txt mysqlclient==2.2.7 \
    && (uv pip uninstall --system python-openid || true) \
    && uv pip install --system python3-openid

FROM base AS app
COPY . .
EXPOSE 8000
ENTRYPOINT ["sh", "docker/entrypoint.sh"]

FROM base AS test
COPY requirements-test.txt .
# Chromium, for the browser tests in apps/test_service_install.py
RUN uv pip install --system -r requirements-test.txt \
    && python -m playwright install --with-deps chromium
COPY . .
ENTRYPOINT ["sh", "docker/run-tests.sh"]

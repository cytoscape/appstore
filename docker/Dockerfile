# Runs the App Store as the target of the external integration suite (make integration-test).
# A test image: Django's dev server with DEBUG on, an SQLite database and seeded data.
FROM python:3.12.7-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv \
    DJANGO_SETTINGS_MODULE=settings.container

# ROOT_URLCONF is 'appstore.urls', so the code must live in a directory named appstore
WORKDIR /srv/appstore

COPY requirements.txt .
# same python-openid swap as the Makefile's build target
RUN uv pip install --system -r requirements.txt \
    && (uv pip uninstall --system python-openid || true) \
    && uv pip install --system python3-openid

COPY . .

EXPOSE 8000
ENTRYPOINT ["sh", "docker/entrypoint.sh"]

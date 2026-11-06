#!/bin/sh
# Builds the database the way the Makefile's build target does, seeds it, then serves on port 8000.
set -e
cd /srv/appstore

mkdir -p build/media build/whoosh_index
for app in apps backend download help search submit_app users; do
    python manage.py makemigrations "$app" --noinput
done
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py seed_integration_data
python manage.py rebuild_index --noinput

exec python manage.py runserver 0.0.0.0:8000 --noreload

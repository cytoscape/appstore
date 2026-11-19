#!/bin/sh
# Runs the Django tests in the tests container of docker/compose.yml (make test): builds what the
# Makefile's build target built on the host, then runs manage.py test against the db container.
set -e
cd /srv/appstore

mkdir -p build/media build/whoosh_index
for app in apps backend download help search submit_app users; do
    python manage.py makemigrations "$app" --noinput
done
python manage.py makemigrations --noinput

exec python manage.py test "$@"

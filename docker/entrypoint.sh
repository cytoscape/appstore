#!/bin/sh
# The integration suite's App Store (the app container of docker/compose.yml): builds the database,
# puts it in apps.cytoscape.org's state, runs the deploy's migrate, seeds it, then serves on port 8000.
set -e
cd /srv/appstore

mkdir -p build/media build/whoosh_index
for app in apps backend download help search submit_app users; do
    python manage.py makemigrations "$app" --noinput
done
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# prod's state: the old unique key on apps_orderedauthor (#160); then the runbook's deploy step,
# whose output integration-test.sh checks
python manage.py add_legacy_author_key
echo "=== deploy: migrate"
python manage.py migrate --noinput

python manage.py seed_integration_data
python manage.py rebuild_index --noinput

exec python manage.py runserver 0.0.0.0:8000 --noreload

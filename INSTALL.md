# Install overview

## Running the tests
Host prerequisites: Docker with Compose, and `make`. Everything else runs in containers
(`docker/compose.yml`): MariaDB, configured as on apps.cytoscape.org, Python with the App Store's
requirements and its MySQL driver, and the browsers.
```
make test
```
This builds the App Store's `test` image (`docker/Dockerfile`), starts an empty MariaDB, generates
the migrations and runs `manage.py test` against it, then removes both containers.

The MariaDB version and SQL mode default to `mariadb:10.11` and MariaDB's strict default. To test
against prod's, read them on the server with
`python manage.py dbshell -- -e "SELECT VERSION(), @@GLOBAL.sql_mode;"` and set `MARIADB_IMAGE`
(e.g. `mariadb:10.5`) and `MARIADB_SQL_MODE` when running `make test` or `make integration-test`.

## Running the integration tests
```
make integration-test
```
For Chromium and then Firefox, this:
1. starts an empty MariaDB and the App Store's `app` image, which migrates and seeds it
2. waits for the App Store to answer
3. runs the Playwright suite in `integration/` in the official Playwright container, which opens
   the App Store on its own `localhost`

The App Store seeds its database with `seed_integration_data`: the `it-admin`, `it-editor` and
`it-other` users, and the `IT …` apps. The suite signs in as those users with the session keys the
seed writes. The report is written to `integration/playwright-report/`.

## Running the App Store locally
```
make runserver
```
This serves the App Store on http://127.0.0.1:8000, on a MariaDB whose data is kept between runs.
`make runserver-reset` removes that data and the generated migrations.

## Legacy setup
This project currently only works with `python 2` and very old django version `django < 1.9`.
This instructions show how to setup a local virtual environment.

## Checkout code base
```
git clone https://github.com/cytoscape/appstore.git CyAppStore
```
The root folder must be named `CyAppStore` so that the relative imports are working.

## Additional requirements
- mysql
- xapian (https://xapian.org/docs/install.html, https://github.com/notanumber/xapian-haystack/blob/master/install_xapian.sh)



## Setup Virtual Environment
``` 
mkvirtualenv appstore --python=python2
(appstore) ./install_xapian.sh 1.4.5
(appstore) pip install gevent
(appstore) pip install -r requirement.txt
```

## Perform the migrations
```
(appstore) python manage.py migrate
```

## Test the server
```
(appstore) python manage.py runserver
```


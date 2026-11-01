# Install overview

## Running the tests
Host prerequisites: [uv](https://docs.astral.sh/uv/) (it provides Python 3.12 and the virtualenv).
```
make test
```
This creates `.venv/` with uv from `requirements.txt` and `requirements-test.txt` (including the Chromium browser for the browser tests), builds `build/` (migrations, search index) and runs `manage.py test`.

On Linux, the browser tests also need Chromium's system libraries. Install them once, before the first `make test` (it needs sudo):
```
make .venv/.installed
.venv/bin/python -m playwright install-deps chromium
make test
```

## Running the integration tests
Host prerequisites: a running Docker engine, Node.js 20 or later, and `curl`.
```
make integration-test
```
This builds the `appstore-it:local` image (`docker/Dockerfile`). Then, for Chromium and then Firefox, it:
1. starts a fresh container on port 8080 (`INTEGRATION_PORT=... make integration-test` to change it)
2. waits for it to answer
3. runs the Playwright suite in `integration/` against it

The container seeds its database with `seed_integration_data`: the `it-admin`, `it-editor` and `it-other` users, and the `IT …` apps. The suite signs in as those users with the session keys the seed writes.

On Linux, Playwright's browsers need system libraries. Install them once (it needs sudo):
```
cd integration && npm ci && npx playwright install-deps chromium firefox
```

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


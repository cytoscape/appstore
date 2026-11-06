# Settings for the integration-test container (docker/Dockerfile).
# The browser reaches the server through the port the container exports, so
# links the pages build from CDN_BASE_URL use that public address.
import os
from settings.local import *

ALLOWED_HOSTS = ['*']

APPSTORE_PUBLIC_URL = os.environ.get('APPSTORE_PUBLIC_URL', 'http://localhost:8080').rstrip('/')
CDN_BASE_URL = APPSTORE_PUBLIC_URL + '/web/'

INTEGRATION_SEED_ENABLED = True

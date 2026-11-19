# Settings for the integration suite's app container (docker/compose.yml), on the database of
# settings.local. Links the pages build from CDN_BASE_URL use the address the browser opens.
import os
from settings.local import *

ALLOWED_HOSTS = ['*']

APPSTORE_PUBLIC_URL = os.environ.get('APPSTORE_PUBLIC_URL', 'http://localhost:8000').rstrip('/')
CDN_BASE_URL = APPSTORE_PUBLIC_URL + '/web/'

INTEGRATION_SEED_ENABLED = True

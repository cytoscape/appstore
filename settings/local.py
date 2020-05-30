
import settings
from settings.base import *
import os
import warnings
warnings.warn("Running local configuration")

DEBUG = True
DJANGO_STATIC_AND_MEDIA = DEBUG
MVN_BIN_PATH = ""
MVN_SETTINGS_PATH = ""
EMAIL_ADDR = ""
CONTACT_EMAIL = "root@localhost"
CONTACT_EMAILS = [CONTACT_EMAIL]
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SITE_DIR = os.path.dirname(os.path.dirname(settings.__file__))
BUILD_DIR = os.path.join(SITE_DIR, 'build')
XAPIAN_INDICES_DIR = os.path.join(SITE_DIR, 'xapian_indices')
SITE_URL = "http://localhost:8000"
SECRET_KEY = "12345"

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BUILD_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"

STATIC_ROOT = BUILD_DIR + "/static/"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
# STATIC_URL = urljoin(SITE_URL, 'static/')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(SITE_DIR, 'static'),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BUILD_DIR, 'sqlite3.db'),
        'TEST': {
            'NAME': 'test_AppStore'
        }
    }
}

INSTALLED_APPS += ('django.contrib.staticfiles', )
# TEMPLATES[0]['DIRS'] = [SITE_DIR]
# TEMPLATES[0]['OPTIONS'] = DEBUG

MIGRATION_MODULES = {
    'download': 'build.appstore.download',
    'submit_app': 'build.appstore.submit_app'
}

# Output all logs
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['appstore'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True,
}

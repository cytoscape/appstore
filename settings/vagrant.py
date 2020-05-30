
from settings.base import *
from urllib import parse
import os
import warnings
warnings.warn("Running vagrant configuration")

ALLOWED_HOSTS = ['localhost', '127.0.0.1', ]

DEBUG = True
DJANGO_STATIC_AND_MEDIA = False

MVN_BIN_PATH = ""
MVN_SETTINGS_PATH = ""
EMAIL_ADDR = ""
CONTACT_EMAIL = "root@localhost"
CONTACT_EMAILS = [CONTACT_EMAIL]
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
SITE_DIR = "/var/www/appstore/"
STATIC_BASE_DIR = "/var/www/html/"
XAPIAN_INDICES_DIR = os.path.join(SITE_DIR, 'xapian_indices')
SITE_URL = "http://localhost:8080"
SECRET_KEY = "12345"

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(STATIC_BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = parse.urljoin(SITE_URL, 'media/')

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(STATIC_BASE_DIR, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
# STATIC_URL = urljoin(SITE_URL, 'static/')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(SITE_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'AppStore',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'USER': 'appstoreuser',
        'PASSWORD': '@@PASSWORD@@',
        'TEST': {
            'NAME': 'test_AppStore'
        }
    }
}

INSTALLED_APPS += ('django.contrib.staticfiles', )
# TEMPLATES[0]['DIRS'] = [SITE_DIR]
# TEMPLATES[0]['OPTIONS'] = DEBUG

# Output all logs
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['appstore'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True,
}
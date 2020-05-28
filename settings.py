import os
from os.path import join as filejoin
try:
    from urllib.parse import urljoin
except ImportError:
     from urlparse import urljoin

SITE_DIR = "/var/www/CyAppStore/"

# credentials provided
try:
    from conf.paths import *
    from conf.emails import *
    from conf.dbs import *
    from conf.apikeys import *
    from conf.socialauth import *
except:
    from conf.mock import *
    # DATABASES = {
    #     'default': {
    #        'NAME': '/var/www/CyAppStore/CyAppStore.sqlite',
    #        'ENGINE': 'django.db.backends.sqlite3',
    #    }
    #
    # }
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'AppStore',
            'HOST': '127.0.0.1',
            'PORT': '3306',
            'USER': 'appstoreuser',
            'PASSWORD': '@@PASSWORD@@',
        }
    }

# Django settings for CyAppStore project.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = True
DJANGO_STATIC_AND_MEDIA = DEBUG

#REVIEW_ALLOW_ANONYMOUS= True
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = False

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = filejoin(SITE_DIR, 'media')
# MEDIA_ROOT = os.path.join(SITE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = urljoin(SITE_URL, 'media/')
# MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
# STATIC_ROOT = ''
STATIC_ROOT = SITE_DIR + "/static/"

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
# STATIC_URL = urljoin(SITE_URL, 'static/')
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
# (This setting is deprecated since Django 1.4--Samad)
# ADMIN_MEDIA_PREFIX = urljoin(SITE_URL, 'static/admin/')

ALLOWED_HOSTS = ['*']

if DJANGO_STATIC_AND_MEDIA:
    # Additional locations of static files
    STATICFILES_DIRS = (
        # Put strings here, like "/home/html/static" or "C:/www/django/static".
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
        filejoin(SITE_DIR, 'static'),
    )

    # List of finder classes that know how to find static files in
    # various locations.
    STATICFILES_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.DefaultStorageFinder',
    )

# the old templates was deprecated in 1.8 and gone after
# here is the new approach
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': SITE_DIR,
        'OPTIONS': {
             'debug': DEBUG,
             'context_processors': [
                 'social_django.context_processors.backends',
                 'social_django.context_processors.login_redirect',
                 'django.core.context_processors.debug',
                 'django.core.context_processors.media',
                 'django.core.context_processors.static',
                 'django.core.context_processors.request',
                 'django.contrib.auth.context_processors.auth',
                 'django.contrib.messages.context_processors.messages'
             ],
             'loaders': [
                 'django.template.loaders.filesystem.Loader',
                 'django.template.loaders.app_directories.Loader'
              ],
         }
    },
]


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
)

ROOT_URLCONF = 'CyAppStore.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'whoosh',
    'haystack',
    'social_django',
    'apps',
    'search',
    'submit_app',
    'users',
    'help',
    'backend',
    'download',
    'CyAppStore'  # this must be included to find root templates
    )

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
    },
}

if DJANGO_STATIC_AND_MEDIA:
    INSTALLED_APPS += ('django.contrib.staticfiles', )

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'mail_admins_always': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'users.views': {
            'handlers': ['mail_admins_always'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

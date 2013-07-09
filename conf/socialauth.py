# settings for social authentication

from urlparse import urljoin
from paths import SITE_URL

SOCIAL_AUTH_COMPLETE_URL_NAME = 'login_done'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'socialauth_associate_complete'
SOCIAL_AUTH_DEFAULT_USERNAME = 'social_auth_user'
LOGIN_URL = urljoin(SITE_URL, 'users/login')
LOGIN_REDIRECT_URL = SITE_URL
LOGOUT_URL = urljoin(SITE_URL, 'users/logout')

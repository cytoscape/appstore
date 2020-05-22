"""
WSGI config for CyAppStore project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys
from os.path import join as filejoin
from django.core.wsgi import get_wsgi_application

SITE_PARENT_DIR = '/var/www'
SITE_DIR = filejoin(SITE_PARENT_DIR, 'CyAppStore')

sys.path.append(SITE_PARENT_DIR)
sys.path.append(SITE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CyAppStore.settings")

application = get_wsgi_application()

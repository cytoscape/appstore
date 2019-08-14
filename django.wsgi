import os
from os.path import join as filejoin
import sys

SITE_PARENT_DIR = '/var/www'
SITE_DIR = filejoin(SITE_PARENT_DIR, 'CyAppStore')

sys.path.append(SITE_PARENT_DIR)
sys.path.append(SITE_DIR)
sys.path.append('/usr/lib/python3/dist-packages')
sys.path.append('/usr/local/lib/python3.6/dist-packages/')
li = ['/usr/local/lib/python2.7/dist-packages','/usr/lib/python2.7/dist-packages']
for i in li:
	try:
		sys.path.remove(i)
	except:
		print()
os.environ['PYTHON_EGG_CACHE'] = filejoin(SITE_DIR, '.python-egg')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

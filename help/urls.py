from django.urls import re_path

from help.views import about
from help.views import contact
from help.views import competitions
from help.views import md
from help.views import getstarted
from help.views import getstarted_app_install

urlpatterns = [
    re_path(r'^about$', about, name='about'),
    re_path(r'^contact$', contact, name='contact'),
    re_path(r'^md$', md, name='md'),
    re_path(r'^getstarted$', getstarted, name='getstarted'),
    re_path(r'^getstarted_app_install$', getstarted_app_install, name='getstarted_app_install'),
]

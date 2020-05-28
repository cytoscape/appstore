from django.conf.urls import url

from help.views import about
from help.views import contact
from help.views import competitions
from help.views import md
from help.views import getstarted
from help.views import getstarted_app_install

urlpatterns = [
    url(r'^about$', about, name='about'),
    url(r'^contact$', contact, name='contact'),
    url(r'^competitions$', competitions, name='competitions'),
    url(r'^md$', md, name='md'),
    url(r'^getstarted$', getstarted, name='getstarted'),
    url(r'^getstarted_app_install$', getstarted_app_install, name='getstarted_app_install'),
]

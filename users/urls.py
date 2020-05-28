from django.conf.urls import include, url

from social_django import urls
from users.views import login
from users.views import login_done
from users.views import logout
urlpatterns = [
    url(r'', include(urls, namespace='social')),
    url(r'login/$', login, name='login'),
    url(r'^login$', login, name='login'),
    url(r'^login/done/([\w-]{1,100})/$', login_done,
        name='login_done'),
    url(r'^logout$', logout, name='logout'),
]

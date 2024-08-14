from django.urls import include, re_path

from social_django import urls
from users.views import login
from users.views import login_done
from users.views import logout
urlpatterns = [
    re_path(r'', include(urls, namespace='social')),
    re_path(r'login/$', login, name='login'),
    re_path(r'^login$', login, name='login'),
    re_path(r'^login/done/([\w-]{1,100})/$', login_done,
        name='login_done'),
    re_path(r'^logout$', logout, name='logout'),
]

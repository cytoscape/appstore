from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'', include('social_django.urls', namespace='social')),
    url(r'login/$', 'users.views.login', name='login'),
    url(r'^login$',                       'users.views.login',        name='login'),
    url(r'^login/done/([\w-]{1,100})/$',  'users.views.login_done',   name='login_done'),
    url(r'^logout$',                      'users.views.logout',       name='logout'),
)

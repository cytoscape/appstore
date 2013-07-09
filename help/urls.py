from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^about$',                     'help.views.about',      name='about'),
    url(r'^contact$',                   'help.views.contact',    name='contact'),
    url(r'^competitions$',              'help.views.competitions',name='competitions'),
    url(r'^md$',                        'help.views.md',         name='md'),
    url(r'^getstarted$',                'help.views.getstarted', name='getstarted'),
    url(r'^getstarted_app_install$',    'help.views.getstarted_app_install', name='getstarted_app_install'),
)

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^all_apps$', 'backend.views.all'),
)

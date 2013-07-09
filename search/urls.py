from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'search.views.search', name='search'),
)

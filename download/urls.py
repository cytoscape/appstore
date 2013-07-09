from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^stats/$',                                      'download.views.all_stats',                   name='all_stats'),
	url(r'^stats/timeline$',                              'download.views.all_stats_timeline'),
	url(r'^stats/geography/all$',                         'download.views.all_stats_geography_all'),
	url(r'^stats/geography/world$',                       'download.views.all_stats_geography_world'),
	url(r'^stats/geography/country/(\w{2})$',             'download.views.all_stats_geography_country'),
    url(r'^stats/(\w{1,100})/$',                          'download.views.app_stats',                   name='app_stats'),
    url(r'^stats/(\w{1,100})/timeline$',                  'download.views.app_stats_timeline'),
    url(r'^stats/(\w{1,100})/geography/all$',             'download.views.app_stats_geography_all'),
    url(r'^stats/(\w{1,100})/geography/world$',           'download.views.app_stats_geography_world'),
    url(r'^stats/(\w{1,100})/geography/country/(\w{2})$', 'download.views.app_stats_country'),
    
	url(r'^(\w{1,100})/(.{1,31})$',                      'download.views.release_download',            name='release_download'),
)

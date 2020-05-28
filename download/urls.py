from django.conf.urls import url

from download.views import all_stats
from download.views import all_stats_timeline
from download.views import all_stats_geography_all
from download.views import all_stats_geography_world
from download.views import all_stats_geography_country
from download.views import app_stats
from download.views import app_stats_timeline
from download.views import app_stats_geography_all
from download.views import app_stats_geography_world
from download.views import app_stats_country
from download.views import release_download

urlpatterns = [
	url(r'^stats/$', all_stats, name='all_stats'),
	url(r'^stats/timeline$', all_stats_timeline),
	url(r'^stats/geography/all$', all_stats_geography_all),
	url(r'^stats/geography/world$', all_stats_geography_world),
	url(r'^stats/geography/country/(\w{2})$', all_stats_geography_country),
	url(r'^stats/(\w{1,100})/$', app_stats, name='app_stats'),
	url(r'^stats/(\w{1,100})/timeline$', app_stats_timeline),
	url(r'^stats/(\w{1,100})/geography/all$', app_stats_geography_all),
	url(r'^stats/(\w{1,100})/geography/world$', app_stats_geography_world),
	url(r'^stats/(\w{1,100})/geography/country/(\w{2})$', app_stats_country),
	url(r'^(\w{1,100})/(.{1,31})$', release_download, name='release_download'),
]

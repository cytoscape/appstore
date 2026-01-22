from django.urls import re_path

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
	re_path(r'^stats/$', all_stats, name='all_stats'),
	re_path(r'^stats/timeline$', all_stats_timeline),
	re_path(r'^stats/geography/all$', all_stats_geography_all),
	re_path(r'^stats/geography/world$', all_stats_geography_world),
	re_path(r'^stats/geography/country/(\w{2})$', all_stats_geography_country),
	re_path(r'^stats/(\w{1,100})/$', app_stats, name='app_stats'),
	re_path(r'^stats/(\w{1,100})/timeline$', app_stats_timeline),
	re_path(r'^stats/(\w{1,100})/geography/all$', app_stats_geography_all),
	re_path(r'^stats/(\w{1,100})/geography/world$', app_stats_geography_world),
	re_path(r'^stats/(\w{1,100})/geography/country/(\w{2})$', app_stats_country),
	re_path(r'^(\w{1,100})/(.{1,31})$', release_download, name='release_download'),
]

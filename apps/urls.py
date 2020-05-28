from django.conf.urls import url

from apps.views import apps_default
from apps.views import all_apps_downloads
from apps.views import all_apps_newest
from apps.views import all_apps
from apps.views import wall_of_apps
from apps.views import apps_with_tag
from apps.views import apps_with_author
from apps.views import app_page
from apps.views import app_page_edit
from apps.views import author_names
from apps.views import institution_names
from download.views import release_download

urlpatterns = [
    url(r'^$', apps_default),
    url(r'^all_$', all_apps_downloads, name='all_apps_downloads'),
    url(r'^all_new$', all_apps_newest, name='all_apps_newest'),
    url(r'^all$', all_apps, name='all_apps'),
    url(r'^wall$', wall_of_apps, name='wall_of_apps'),
    url(r'^with_tag/(\w{1,100})$', apps_with_tag, name='tag_page'),
    url(r'^with_author/(.{1,300})$', apps_with_author, name='author_page'),
    url(r'^(\w{1,100})$', app_page, name='app_page'),
    url(r'^(\w{1,100})/edit$', app_page_edit, name='app_page_edit'),
    url(r'^(\w{1,100})/author_names$', author_names),
    url(r'^(\w{1,100})/institution_names$', institution_names),
    url(r'^(\w{1,100})/download/(.{1,31})$', release_download), # old url for downloads
]

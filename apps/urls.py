from django.urls import re_path

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
    re_path(r'^$', apps_default),
    re_path(r'^all_$', all_apps_downloads, name='all_apps_downloads'),
    re_path(r'^all_new$', all_apps_newest, name='all_apps_newest'),
    re_path(r'^all$', all_apps, name='all_apps'),
    re_path(r'^wall$', wall_of_apps, name='wall_of_apps'),
    re_path(r'^with_tag/(\w{1,100})$', apps_with_tag, name='tag_page'),
    re_path(r'^with_author/(.{1,300})$', apps_with_author, name='author_page'),
    re_path(r'^(\w{1,100})$', app_page, name='app_page'),
    re_path(r'^(\w{1,100})/edit$', app_page_edit, name='app_page_edit'),
    re_path(r'^(\w{1,100})/author_names$', author_names),
    re_path(r'^(\w{1,100})/institution_names$', institution_names),
    re_path(r'^(\w{1,100})/download/(.{1,31})$', release_download), # old url for downloads
]

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$',                                'apps.views.apps_default'),
    url(r'^all$',                             'apps.views.all_apps',             name='all_apps'),
    url(r'^wall$',                            'apps.views.wall_of_apps',         name='wall_of_apps'),
    url(r'^with_tag/(\w{1,100})$',            'apps.views.apps_with_tag',        name='tag_page'),
    url(r'^with_author/(.{1,300})$',          'apps.views.apps_with_author',     name='author_page'),
    url(r'^(\w{1,100})$',                     'apps.views.app_page',             name='app_page'),
    url(r'^(\w{1,100})/edit$',                'apps.views.app_page_edit',        name='app_page_edit'),
    url(r'^(\w{1,100})/download/(.{1,31})$',  'download.views.release_download'), # old url for downloads
)

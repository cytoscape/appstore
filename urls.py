from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings

from apps.views import apps_default

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('users.urls')),
    url(r'^$', apps_default, name='default-page'),
    url(r'^apps/', include('apps.urls')),
    url(r'^search', include('haystack.urls')),
    url(r'^download/', include('download.urls')),
    url(r'^submit_app/', include('submit_app.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^help/',  include('help.urls')),
    url(r'^backend/', include('backend.urls')),
]

if settings.DJANGO_STATIC_AND_MEDIA:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

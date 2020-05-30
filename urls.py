import logging

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings

from apps.views import apps_default

from django.contrib import admin
admin.autodiscover()

logger = logging.getLogger(__name__)

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

# If DJANGO_STATIC_AND_MEDIA then have Django serve
# media content directly which appears to only work if the
# MEDIA_URL is set to /media/
# https://docs.djangoproject.com/en/2.1/howto/static-files/#serving-files-uploaded-by-a-user-during-development
#
if settings.DJANGO_STATIC_AND_MEDIA:
    logger.info('Development server running letting Django serve media '
                'at url: ' + settings.MEDIA_URL + ' via root: ' +
                settings.MEDIA_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
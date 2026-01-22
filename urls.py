import logging

from django.urls import include, re_path
from django.conf.urls.static import static
from django.conf import settings

from apps.views import apps_default

from django.contrib import admin
admin.autodiscover()

logger = logging.getLogger(__name__)

urlpatterns = [
    # Uncomment the next line to enable the admin:
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/', include('users.urls')),
    re_path(r'^$', apps_default, name='default-page'),
    re_path(r'^apps/', include('apps.urls')),
    re_path(r'^search', include('haystack.urls')),
    re_path(r'^download/', include('download.urls')),
    re_path(r'^submit_app/', include('submit_app.urls')),
    re_path(r'^users/', include('users.urls')),
    re_path(r'^help/',  include('help.urls')),
    re_path(r'^backend/', include('backend.urls')),
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
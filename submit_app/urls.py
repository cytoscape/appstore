from django.urls import re_path

from submit_app.views import submit_app
from submit_app.views import pending_apps
from submit_app.views import cy2x_plugins
from submit_app.views import confirm_submission
from submit_app.views import submit_api
from submit_app.views import artifact_exists
from submit_app.views import platform_select
from submit_app.views import submit_service_app
from submit_app.views import service_app_confirm
from submit_app.views import submit_web_url
from submit_app.views import submit_web_bundle


urlpatterns = [
    re_path(r'^$', submit_app, name='submit-app'),
    re_path(r'^select_platform$', platform_select, name='platform-select'),
    re_path(r'^pending$', pending_apps, name='pending-apps'),
    re_path(r'^cy2xplugins$', cy2x_plugins, name='cy2x-plugins'),
    re_path(r'^confirm/(\d{1,5})$', confirm_submission, name='confirm-submission'),
    re_path(r'^submit_api/(\d{1,5})$', submit_api, name='submit-api'),
    re_path(r'^artifact_exists$', artifact_exists),
    re_path(r'^submit_service_app$', submit_service_app, name='submit-service-app'),
    re_path(r'^confirm_service/(\d{1,5})$', service_app_confirm, name='confirm-service'),
    re_path(r'^submit_web_url$', submit_web_url, name='submit-web-url'),
    re_path(r'^submit_web_bundle$', submit_web_bundle, name='submit-web-bundle'),
]

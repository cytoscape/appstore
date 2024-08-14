from django.urls import re_path

from submit_app.views import submit_app
from submit_app.views import pending_apps
from submit_app.views import cy2x_plugins
from submit_app.views import confirm_submission
from submit_app.views import submit_api
from submit_app.views import artifact_exists

urlpatterns = [
    re_path(r'^$', submit_app, name='submit-app'),
    re_path(r'^pending$', pending_apps, name='pending-apps'),
    re_path(r'^cy2xplugins$', cy2x_plugins, name='cy2x-plugins'),
    re_path(r'^confirm/(\d{1,5})$', confirm_submission, name='confirm-submission'),
    re_path(r'^submit_api/(\d{1,5})$', submit_api, name='submit-api'),
    re_path(r'^artifact_exists$', artifact_exists),
]

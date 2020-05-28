from django.conf.urls import url

from submit_app.views import submit_app
from submit_app.views import pending_apps
from submit_app.views import cy2x_plugins
from submit_app.views import confirm_submission
from submit_app.views import submit_api
from submit_app.views import artifact_exists

urlpatterns = [
    url(r'^$', submit_app, name='submit-app'),
    url(r'^pending$', pending_apps, name='pending-apps'),
    url(r'^cy2xplugins$', cy2x_plugins, name='cy2x-plugins'),
    url(r'^confirm/(\d{1,5})$', confirm_submission, name='confirm-submission'),
    url(r'^submit_api/(\d{1,5})$', submit_api, name='submit-api'),
    url(r'^artifact_exists$', artifact_exists),
]

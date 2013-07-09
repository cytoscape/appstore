from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$',                      'submit_app.views.submit_app',         name='submit-app'),
    url(r'^pending$',               'submit_app.views.pending_apps',       name='pending-apps'),
    url(r'^confirm/(\d{1,5})$',     'submit_app.views.confirm_submission', name='confirm-submission'),
    url(r'^submit_api/(\d{1,5})$',  'submit_app.views.submit_api',         name='submit-api'),
    url(r'^artifact_exists$',       'submit_app.views.artifact_exists'),
)

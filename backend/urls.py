from django.conf.urls import url

from backend.views import all

urlpatterns = [
    url(r'^all_apps$', all),
]

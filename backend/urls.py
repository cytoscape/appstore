from django.conf.urls import url

from backend.views import all_apps_func

urlpatterns = [
    url(r'^all_apps$', all_apps_func),
]

from django.urls import re_path

from backend.views import all_apps_func

urlpatterns = [
    re_path(r'^all_apps$', all_apps_func),
]

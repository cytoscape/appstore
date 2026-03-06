from django.urls import path

from .views import (
    SubmitServiceAppView,
    ServiceAppListView,
    ServiceAppDetailView,
    service_apps_config,
)

app_name = "serviceapps"

urlpatterns = [
    path("submit/service-app/", SubmitServiceAppView.as_view(), name="submit"),
    path("service-apps/", ServiceAppListView.as_view(), name="list"),
    path("service-apps/<int:pk>/", ServiceAppDetailView.as_view(), name="detail"),
    path("api/service-apps/config", service_apps_config, name="config"),
]

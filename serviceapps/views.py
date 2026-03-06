import logging

import requests
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, ListView, DetailView

from .forms import ServiceAppSubmitForm
from .models import ServiceApp

logger = logging.getLogger(__name__)

SPEC_TIMEOUT = 8

REQUIRED_TOP_KEYS = [
    "name",
    "description",
    "version",
    "parameters",
    "serviceInputDefinition",
    "cyWebActions",
    "cyWebMenuItem",
]


def _fetch_json(url):
    r = requests.get(url, timeout=SPEC_TIMEOUT,
                     headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


class SubmitServiceAppView(FormView):
    template_name = "serviceapps/submit.html"
    form_class = ServiceAppSubmitForm

    def get_success_url(self):
        return reverse("serviceapps:list")

    def form_valid(self, form):
        base = form.cleaned_data["service_url"].rstrip("/")

        try:
            meta = _fetch_json(base + "/")
        except Exception as e:
            form.add_error("service_url", f"Could not fetch '/': {e}")
            return self.form_invalid(form)

        missing = [k for k in REQUIRED_TOP_KEYS if k not in meta]
        if missing:
            form.add_error("service_url",
                           f"Missing keys: {', '.join(missing)}")
            return self.form_invalid(form)

        try:
            status_json = _fetch_json(base + "/status")
        except Exception as e:
            form.add_error("service_url",
                           f"Could not fetch '/status': {e}")
            return self.form_invalid(form)

        last_status = ("ok" if status_json.get("status") == "ok"
                       else "unavailable")

        sa, _ = ServiceApp.objects.get_or_create(service_url=base)
        sa.metadata = meta
        sa.display_name = meta.get("name", "")
        sa.description = meta.get("description", "")
        sa.author = meta.get("author", "")
        sa.version = meta.get("version", "")
        sa.last_status = last_status
        sa.last_checked = timezone.now()
        sa.is_active = True
        sa.save()

        return super().form_valid(form)


class ServiceAppListView(ListView):
    model = ServiceApp
    template_name = "serviceapps/list.html"
    context_object_name = "services"

    def get_queryset(self):
        qs = ServiceApp.objects.filter(is_active=True)
        health = self.request.GET.get("health")
        if health:
            qs = qs.filter(last_status=health)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(display_name__icontains=q)
        return qs


class ServiceAppDetailView(DetailView):
    model = ServiceApp
    template_name = "serviceapps/detail.html"

    def get_queryset(self):
        return ServiceApp.objects.filter(is_active=True)


def service_apps_config(request):
    qs = ServiceApp.objects.filter(is_active=True, last_status="ok")
    return JsonResponse([sa.as_app_definition() for sa in qs], safe=False)

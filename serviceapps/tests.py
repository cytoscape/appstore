from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, Mock

from .models import ServiceApp

ROOT_META = {
    "name": "Demo Service",
    "description": "Example",
    "version": "1.0.0",
    "parameters": [],
    "serviceInputDefinition": {},
    "cyWebActions": [],
    "cyWebMenuItem": {"title": "Tools/Demo"},
}

STATUS_OK = {"status": "ok"}


class ServiceAppModelTests(TestCase):
    def test_str_with_display_name(self):
        sa = ServiceApp(display_name="My App", service_url="https://example.org")
        self.assertEqual(str(sa), "My App")

    def test_str_without_display_name(self):
        sa = ServiceApp(service_url="https://example.org")
        self.assertEqual(str(sa), "https://example.org")

    def test_as_app_definition(self):
        sa = ServiceApp(service_url="https://example.org/demo")
        self.assertEqual(sa.as_app_definition(), {"url": "https://example.org/demo"})


class SubmitServiceAppTests(TestCase):
    @patch("serviceapps.views.requests.get")
    def test_submit_valid_service(self, mget):
        def _resp(url, *args, **kwargs):
            mock = Mock()
            mock.raise_for_status = lambda: None
            if url.endswith("/status"):
                mock.json = lambda: STATUS_OK
            else:
                mock.json = lambda: ROOT_META
            return mock
        mget.side_effect = _resp

        resp = self.client.post(
            reverse("serviceapps:submit"),
            {"service_url": "https://example.org/demo"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(ServiceApp.objects.count(), 1)

        sa = ServiceApp.objects.first()
        self.assertEqual(sa.display_name, "Demo Service")
        self.assertEqual(sa.last_status, "ok")

    @patch("serviceapps.views.requests.get")
    def test_submit_missing_keys(self, mget):
        def _resp(url, *args, **kwargs):
            mock = Mock()
            mock.raise_for_status = lambda: None
            mock.json = lambda: {"name": "Incomplete"}
            return mock
        mget.side_effect = _resp

        resp = self.client.post(
            reverse("serviceapps:submit"),
            {"service_url": "https://example.org/bad"},
        )
        self.assertEqual(resp.status_code, 200)  # re-renders form with errors
        self.assertEqual(ServiceApp.objects.count(), 0)

    @patch("serviceapps.views.requests.get")
    def test_submit_unreachable(self, mget):
        mget.side_effect = Exception("Connection refused")

        resp = self.client.post(
            reverse("serviceapps:submit"),
            {"service_url": "https://example.org/down"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ServiceApp.objects.count(), 0)


class ServiceAppConfigTests(TestCase):
    def test_config_returns_active_ok_apps(self):
        ServiceApp.objects.create(
            service_url="https://a.example.org",
            display_name="A",
            is_active=True,
            last_status="ok",
        )
        ServiceApp.objects.create(
            service_url="https://b.example.org",
            display_name="B",
            is_active=True,
            last_status="error",
        )
        ServiceApp.objects.create(
            service_url="https://c.example.org",
            display_name="C",
            is_active=False,
            last_status="ok",
        )

        resp = self.client.get(reverse("serviceapps:config"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["url"], "https://a.example.org")


class ServiceAppListTests(TestCase):
    def test_list_shows_only_active(self):
        ServiceApp.objects.create(
            service_url="https://active.example.org",
            display_name="Active",
            is_active=True,
            last_status="ok",
        )
        ServiceApp.objects.create(
            service_url="https://inactive.example.org",
            display_name="Inactive",
            is_active=False,
            last_status="ok",
        )

        resp = self.client.get(reverse("serviceapps:list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Active")
        self.assertNotContains(resp, "Inactive")

    def test_list_filter_by_health(self):
        ServiceApp.objects.create(
            service_url="https://ok.example.org",
            display_name="OK App",
            is_active=True,
            last_status="ok",
        )
        ServiceApp.objects.create(
            service_url="https://err.example.org",
            display_name="Err App",
            is_active=True,
            last_status="error",
        )

        resp = self.client.get(reverse("serviceapps:list"), {"health": "ok"})
        self.assertContains(resp, "OK App")
        self.assertNotContains(resp, "Err App")


class ServiceAppDetailTests(TestCase):
    def test_detail_active_app(self):
        sa = ServiceApp.objects.create(
            service_url="https://detail.example.org",
            display_name="Detail App",
            is_active=True,
            last_status="ok",
        )
        resp = self.client.get(reverse("serviceapps:detail", args=[sa.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Detail App")

    def test_detail_inactive_app_404(self):
        sa = ServiceApp.objects.create(
            service_url="https://gone.example.org",
            display_name="Gone",
            is_active=False,
            last_status="ok",
        )
        resp = self.client.get(reverse("serviceapps:detail", args=[sa.pk]))
        self.assertEqual(resp.status_code, 404)

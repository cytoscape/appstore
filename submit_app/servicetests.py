import socket
import json
from unittest.mock import patch, MagicMock 
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase 
from .models import ServiceAppPending
from apps.models import App, Platform, Author, ServiceRelease
from .servicechecker import (
    ServiceCheckError,
    _is_private_ip,
    check_reachable,
    check_metadata,
    check_service_status,
)


User = get_user_model()

class serviceViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="submitter", password="password")
        self.client.force_login(self.user)
        self.url = reverse('submit-service-app')

    def test_get_service_upload_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'service_upload_form.html')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        #self.assertRedirects(response, reverse('login'))

    def test_missing_service_url_shows_error(self):
        response = self.client.post(self.url, {'service_url': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    @patch("submit_app.views.check_reachable")
    def test_service_check_error_shows_message(self, mock_check):
        mock_check.side_effect = ServiceCheckError("Service check failed")
        response = self.client.post(self.url, {'service_url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    @patch("submit_app.views.check_reachable")
    def test_unexpected_exceptions_caught(self, mock_check):
        mock_check.side_effect = RuntimeError("Boom")
        response = self.client.post(self.url, {'service_url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)

    @patch("submit_app.views.check_reachable")
    def test_invalid_version_format_rejected(self, mock_check):
        mock_check.return_value = {
            'author': 'Test Author',
            'version': 'not-a-version',
            'name': 'Test Service',
        }

        response = self.client.post(self.url, {'service_url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Service URL is required", response.context['error'])
        self.assertFalse(ServiceAppPending.objects.exists())

    @patch("submit_app.views.check_reachable")
    def test_two_part_version_accepted(self, mock_check):
        mock_check.return_value = {
            'author': 'Test Author',
            'version': '1.0',
            'name': 'My Service',
        }
        response = self.client.post(self.url, {'service_url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)  
        self.assertTrue(ServiceAppPending.objects.filter(name='My Service', version='1.0').exists())

    @patch("submit_app.views.check_reachable")
    def test_three_part_version_accepted(self, mock_check):
        mock_check.return_value = {
            'author': 'Test Author',
            'version': '1.0.0',
            'name': 'My Service 2',
        }

        response = self.client.post(self.url, {'service_url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ServiceAppPending.objects.filter(name='My Service 2', version='1.0.0').exists())

    @patch("submit_app.views.check_reachable")
    def test_existing_apps_block_non_editors(self, mock_check):
        mock_check.return_value = {
            "fullname": "Existing Service",
            "name": "existing-service",
            "authors": ["John"],
            "version": "1.0.0",
            "description": "Test service"
        }

        other_user = User.objects.create_user(
            username="other",
            password="password"
        )
        self.client.login(
            username="other",
            password="password"
        )

        app = App.objects.create(
            name="Existing Service",
            platform=Platform.SERVICE,
            has_releases=True
        )

        author = Author.objects.create(name="John")
        app.authors.add(author)

        response = self.client.post(self.url,{"service-url": "http://example.com/meta"})

        self.assertEqual(response.status_code, 200) #redirect to app page
        self.assertIn("not an editor", response.context["error"])

    @patch("submit_app.views.check_reachable")
    def test_existing_apps_allow_editors(self, mock_check):
        app = App.objects.create(fullname="My App", name="my-app", platform=Platform.SERVICE)
        app.editors.add(self.user)
        mock_check.return_value = {
            'author': 'Test Author',
            'version': '1.0.0',
            'name': 'my-app',
        }
        response = self.client.post(self.url, {"service-url": "http://example.com/meta"})
        self.assertEqual(response.status_code, 302)  # Redirect to submission status

    @patch("submit_app.views.check_reachable")
    def test_duplicate_pending_submission_rejected(self, mock_check):
        mock_check.return_value = {
            'author': 'Test Author',
            'version': '1.0.0',
            'name': 'my-app',
        }
        ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
            author="Test Author",
            name="my-app",
        )
        response = self.client.post(self.url, {"service-url": "http://example.com/meta"})
        self.assertEqual(response.status_code, 200) #redirect to submission page with error message
        self.assertIn("already has a pending submission", response.context["error"])

    @patch("submit_app.views.check_reachable")
    def successful_submission_redirects_to_confirm(self, mock_check):
        mock_check.return_value = {
            'author': 'Test Arthur',
            'version': '1.0.0',
            'name': 'my-app',
        }

        response = self.client.post(self.url, {"service-url": "http://example.com/meta"})
        pending = ServiceAppPending.objects.get(name="my-app", version="1.0.0")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('submission_status', args=[pending.id]))
        self.assertEqual(pending.status, ServiceAppPending.Status.PENDING_CHECKER)
        self.assertEqual(pending.author, 'Test Arthur') 
        self.assertEqual(pending.name, 'my-app')

    
    @patch("submit_app.views.check_reachable")
    def test_race_condition_error(self, mock_check):
        # Simulates two concurrent submissions for the same name slipping
        # past the .exists() check and colliding on the DB unique constraint.
        mock_check.return_value = {
            'author': 'Jane',
            'Version':'1.0.0',
            'name': 'service-app'
        }

        ServiceAppPending.objects.create(submitter=self.user, fullname="My App", name="my-app", version="0.9.0")
        with patch(
            "submit_app.models.ServiceAppPending.objects.filter"
        ) as mock_filter:
            mock_filter.return_value.exists.return_value = False  # bypass pre-check
            response = self.client.post(self.url, {"service-url": "http://example.com/meta"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("already pending review", response.context["error"])

        
class serviceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="submitter", password="password")

    def test_default_pending_status_is_pending_checker(self):
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
            metadata={"name": "My App", "version": "1.0.0"},
        )
        self.assertEqual(pending.status, ServiceAppPending.Status.PENDING_CHECKER)

    def test_name_uniqueness_enforced(self):
        ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ServiceAppPending.objects.create(
                    submitter=self.user,
                    fullname="My App Again",
                    name="my-app",  # duplicate
                    version="1.0.1",
                    service_endpoint="http://example.com/meta2",
                )

    def test_status_transitions_are_valid_choices(self):
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app-2",
            version="1.0.0",
        )
        for status in (
            ServiceAppPending.Status.CHECKER_VALIDATED,
            ServiceAppPending.Status.CHECKER_FAILED,
            ServiceAppPending.Status.PENDING_REVIEW,
        ):
            pending.status = status
            pending.save()
            pending.refresh_from_db()
            self.assertEqual(pending.status, status)

    def test_ordering_is_newest_first(self):
        first = ServiceAppPending.objects.create(
            submitter=self.user, fullname="A", name="a", version="1.0"
        )
        second = ServiceAppPending.objects.create(
            submitter=self.user, fullname="B", name="b", version="1.0"
        )
        names = list(ServiceAppPending.objects.values_list("name", flat=True))
        self.assertEqual(names, [second.name, first.name])

class serviceReleaseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="submitter", password="password")
        self.app = App.objects.create(fullname="Service App", name="serviceapp", platform=Platform.SERVICE)
    
    def test_make_service_release_creates_release(self):
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="myapp",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
            author="Jane",
            citation="http://example.com/cite",
            documentation="http://example.com/docs",
            metadata={"name": "My App", "version": "1.0.0"},
        )
 
        pending.make_service_release(self.app)
 
        release = ServiceRelease.objects.get(app=self.app, version="1.0.0")
        self.assertEqual(release.service_endpoint, "http://example.com/meta")
        self.assertTrue(release.active)
        self.assertEqual(release.metadata, {"name": "My App", "version": "1.0.0"})


    def test_make_service_release_is_idempotent_per_version(self):
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
        )
        pending.make_service_release(self.app)
        pending.service_endpoint = "http://example.com/meta-updated"
        pending.make_service_release(self.app)
 
        self.assertEqual(
            ServiceRelease.objects.filter(app=self.app, version="1.0.0").count(), 1
        )
        release = ServiceRelease.objects.get(app=self.app, version="1.0.0")
        self.assertEqual(release.service_endpoint, "http://example.com/meta-updated")

    def test_make_service_release_updates_app_release_flags(self):
        self.app.has_releases = False
        self.app.save()
 
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app",
            version="2.0.0",
            service_endpoint="http://example.com/meta",
        )
        pending.make_service_release(self.app)
 
        self.app.refresh_from_db()
        self.assertTrue(self.app.has_releases)
        self.assertIsNotNone(self.app.latest_release_date)
 
    def test_make_service_release_handles_blank_optional_fields(self):
        pending = ServiceAppPending.objects.create(
            submitter=self.user,
            fullname="My App",
            name="my-app",
            version="1.0.0",
            service_endpoint="http://example.com/meta",
            author=None,
            citation="",
            documentation=None,
        )
        pending.make_service_release(self.app)
        release = ServiceRelease.objects.get(app=self.app, version="1.0.0")
        self.assertEqual(release.citation, "")
 
    def test_service_release_requires_endpoint(self):
        # service_endpoint has blank=False; confirm empty string fails full_clean
        release = ServiceRelease(app=self.app, version="9.9.9", service_endpoint="")
        with self.assertRaises(Exception):
            release.full_clean()


def make_response(status_code=200, chunks=None, json_body=None):
    resp = MagicMock()
    resp.status_code = status_code

    if chunks is None and json_body is not None:
        chunks = [json.dumps(json_body).encode()]
    resp.iter_content.return_value = chunks or []
 
    if json_body is not None:
        resp.json.return_value = json_body
 
    def raise_for_status():
        if status_code >= 400:
            import requests
            raise requests.HTTPError(f"{status_code} error")
    resp.raise_for_status.side_effect = raise_for_status
 
    return resp

class IsPrivateIpTests(TestCase):
 
    @patch("submit_app.servicechecker.socket.gethostbyname")
    def test_private_ip_detected(self, mock_resolve):
        mock_resolve.return_value = "192.168.1.5"
        self.assertTrue(_is_private_ip("internal.local"))
 
    @patch("submit_app.servicechecker.socket.gethostbyname")
    def test_loopback_detected(self, mock_resolve):
        mock_resolve.return_value = "127.0.0.1"
        self.assertTrue(_is_private_ip("localhost"))
 
    @patch("submit_app.servicechecker.socket.gethostbyname")
    def test_link_local_detected(self, mock_resolve):
        mock_resolve.return_value = "169.254.1.1"
        self.assertTrue(_is_private_ip("linklocal.example"))
 
    @patch("submit_app.servicechecker.socket.gethostbyname")
    def test_public_ip_not_private(self, mock_resolve):
        mock_resolve.return_value = "8.8.8.8"
        self.assertFalse(_is_private_ip("dns.google"))
 
    @patch("submit_app.servicechecker.socket.gethostbyname")
    def test_unresolvable_host_raises(self, mock_resolve):
        mock_resolve.side_effect = socket.gaierror("Name or service not known")
        with self.assertRaises(ServiceCheckError):
            _is_private_ip("does-not-exist.invalid")


class CheckReachableTests(TestCase):
 
    def test_missing_hostname_raises(self):
        with self.assertRaises(ServiceCheckError):
            check_reachable("not-a-url")
 
    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ServiceCheckError):
            check_reachable("ftp://example.com/service")
 
    @patch("submit_app.servicechecker._is_private_ip", return_value=True)
    def test_private_ip_blocked_by_default(self, _mock_private):
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://internal.example.com")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=True)
    def test_private_ip_allowed_when_flagged(self, _mock_private, mock_get):
        mock_get.return_value = make_response(
            json_body={"name": "My App", "version": "1.0"}
        )
        metadata = check_reachable("http://localhost:8000/meta", allow_local=True)
        self.assertEqual(metadata["name"], "My App")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_request_exception_wrapped(self, _mock_private, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError("refused")
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://example.com/meta")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_non_200_status_raises(self, _mock_private, mock_get):
        mock_get.return_value = make_response(status_code=404, chunks=[b"{}"])
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://example.com/meta")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_response_too_large_raises(self, _mock_private, mock_get):
        big_chunk = b"x" * 5000
        mock_get.return_value = make_response(status_code=200, chunks=[big_chunk])
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://example.com/meta", maxbytes=4096)
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_invalid_json_raises(self, _mock_private, mock_get):
        mock_get.return_value = make_response(status_code=200, chunks=[b"not json"])
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://example.com/meta")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_missing_required_fields_raises(self, _mock_private, mock_get):
        mock_get.return_value = make_response(json_body={"name": "My App"})  # no version
        with self.assertRaises(ServiceCheckError):
            check_reachable("http://example.com/meta")
 
    @patch("submit_app.servicechecker.requests.get")
    @patch("submit_app.servicechecker._is_private_ip", return_value=False)
    def test_valid_metadata_returned(self, _mock_private, mock_get):
        mock_get.return_value = make_response(
            json_body={"name": "My App", "version": "1.2.3", "author": "Jane"}
        )
        metadata = check_reachable("http://example.com/meta")
        self.assertEqual(metadata["version"], "1.2.3")
        self.assertEqual(metadata["author"], "Jane")
 
    @patch("submit_app.servicechecker.check_reachable")
    def test_check_metadata_delegates_to_check_reachable(self, mock_reachable):
        mock_reachable.return_value = {"name": "x", "version": "1.0"}
        result = check_metadata("http://example.com/meta", allow_local=True)
        mock_reachable.assert_called_once_with(
            "http://example.com/meta", allow_local=True
        )
        self.assertEqual(result["name"], "x")
 
 
class CheckServiceStatusTests(TestCase):
 
    @patch("submit_app.servicechecker.requests.get")
    def test_ok_status_returns_dict(self, mock_get):
        mock_get.return_value = make_response(
            status_code=200, json_body={"status": "ok"}
        )
        result = check_service_status("http://example.com/service")
        self.assertEqual(result["status"], "ok")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_status_url_has_slash_appended_correctly(self, mock_get):
        mock_get.return_value = make_response(
            status_code=200, json_body={"status": "ok"}
        )
        check_service_status("http://example.com/service/")
        called_url = mock_get.call_args[0][0]
        self.assertEqual(called_url, "http://example.com/service/status")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_request_exception_wrapped(self, mock_get):
        import requests
        mock_get.side_effect = requests.Timeout("timed out")
        with self.assertRaises(ServiceCheckError):
            check_service_status("http://example.com/service")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_non_dict_response_raises(self, mock_get):
        mock_get.return_value = make_response(status_code=200, json_body=["oops"])
        with self.assertRaises(ServiceCheckError):
            check_service_status("http://example.com/service")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_missing_status_field_raises(self, mock_get):
        mock_get.return_value = make_response(status_code=200, json_body={"ok": True})
        with self.assertRaises(ServiceCheckError):
            check_service_status("http://example.com/service")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_non_ok_status_value_raises(self, mock_get):
        mock_get.return_value = make_response(
            status_code=200, json_body={"status": "degraded"}
        )
        with self.assertRaises(ServiceCheckError):
            check_service_status("http://example.com/service")
 
    @patch("submit_app.servicechecker.requests.get")
    def test_non_200_http_status_raises(self, mock_get):
        mock_get.return_value = make_response(
            status_code=500, json_body={"status": "ok"}
        )
        with self.assertRaises(ServiceCheckError):
            check_service_status("http://example.com/service")
import datetime
import http.client
import json
from urllib.parse import urlparse

from django.test import LiveServerTestCase, TestCase

from apps.models import App, Platform, Release, ServiceRelease, WebBundleRelease
from download.models import Download, ReleaseDownloadsByDate
from download.models import ServiceDownload, ServiceReleaseDownloadsByDate
from download.models import WebBundleDownload, WebBundleReleaseDownloadsByDate


class DownloadFixtureMixin:
    """Service, web and desktop apps with releases, shared by the download tests."""

    def create_fixtures(self):
        self.service_app = App.objects.create(name='svcapp', fullname='Service App',
                                              platform=Platform.SERVICE, active=True)
        self.service_release = ServiceRelease.objects.create(
            app=self.service_app, version='1.0.0',
            service_endpoint='https://service.example.org/svcapp')
        self.inactive_service_release = ServiceRelease.objects.create(
            app=self.service_app, version='0.9.0',
            service_endpoint='https://service.example.org/svcapp-old', active=False)

        self.web_app = App.objects.create(name='webapp', fullname='Web App',
                                          platform=Platform.WEB, active=True)
        self.web_release = WebBundleRelease.objects.create(
            app=self.web_app, version='2.0.0', active=True, bundle_hash='abc123')

        self.desktop_app = App.objects.create(name='jarapp', fullname='Jar App',
                                              platform=Platform.DESKTOP, active=True)
        self.desktop_release = Release.objects.create(
            app=self.desktop_app, version='3.0.0', works_with='3.10')

    def install_url(self, app, version, client=None):
        url = '/download/install/%s/%s' % (app.name, version)
        return url + '?client=%s' % client if client else url


class ReleaseInstallTestCase(DownloadFixtureMixin, TestCase):

    def setUp(self):
        self.create_fixtures()
        self.today = datetime.date.today()

    def assert_service_counts(self, count):
        self.service_app.refresh_from_db()
        self.assertEqual(count, self.service_app.downloads)
        self.assertEqual(count, ServiceDownload.objects.filter(release=self.service_release).count())
        by_release = ServiceReleaseDownloadsByDate.objects.get(release=self.service_release, when=self.today)
        self.assertEqual(count, by_release.count)
        daily_total = ServiceReleaseDownloadsByDate.objects.get(release=None, when=self.today)
        self.assertEqual(count, daily_total.count)

    def assert_nothing_recorded(self):
        for app in (self.service_app, self.web_app):
            app.refresh_from_db()
            self.assertEqual(0, app.downloads)
        self.assertEqual(0, ServiceDownload.objects.count())
        self.assertEqual(0, ServiceReleaseDownloadsByDate.objects.count())
        self.assertEqual(0, WebBundleDownload.objects.count())
        self.assertEqual(0, WebBundleReleaseDownloadsByDate.objects.count())

    def test_desktop_install_records_and_returns_204(self):
        response = self.client.get(self.install_url(self.service_app, '1.0.0', 'desktop'))
        self.assertEqual(204, response.status_code)
        self.assertNotIn('Location', response)
        self.assertEqual(b'', response.content)
        self.assert_service_counts(1)

    def test_repeat_desktop_installs_increment_existing_counters(self):
        self.client.get(self.install_url(self.service_app, '1.0.0', 'desktop'))
        response = self.client.get(self.install_url(self.service_app, '1.0.0', 'desktop'))
        self.assertEqual(204, response.status_code)
        self.assert_service_counts(2)
        self.assertEqual(2, ServiceReleaseDownloadsByDate.objects.count())

    def test_desktop_install_via_apps_route(self):
        response = self.client.get('/apps/svcapp/install/1.0.0?client=desktop')
        self.assertEqual(204, response.status_code)
        self.assert_service_counts(1)

    def test_cytoscape_web_install_unchanged(self):
        response = self.client.get(self.install_url(self.service_app, '1.0.0'))
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.service_release.install_url, response['Location'])
        self.assert_service_counts(1)

    def test_unknown_client_falls_back_to_cytoscape_web_install(self):
        response = self.client.get(self.install_url(self.service_app, '1.0.0', 'other'))
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.service_release.install_url, response['Location'])
        self.assert_service_counts(1)

    def test_desktop_install_of_inactive_release_is_404(self):
        response = self.client.get(self.install_url(self.service_app, '0.9.0', 'desktop'))
        self.assertEqual(404, response.status_code)
        self.assert_nothing_recorded()

    def test_desktop_install_of_unknown_version_is_404(self):
        response = self.client.get(self.install_url(self.service_app, '9.9.9', 'desktop'))
        self.assertEqual(404, response.status_code)
        self.assert_nothing_recorded()

    def test_desktop_install_of_web_app_is_404(self):
        response = self.client.get(self.install_url(self.web_app, '2.0.0', 'desktop'))
        self.assertEqual(404, response.status_code)
        self.assert_nothing_recorded()

    def test_web_app_install_unchanged(self):
        response = self.client.get(self.install_url(self.web_app, '2.0.0'))
        self.assertEqual(302, response.status_code)
        self.assertEqual(self.web_release.install_url, response['Location'])
        self.web_app.refresh_from_db()
        self.assertEqual(1, self.web_app.downloads)
        self.assertEqual(1, WebBundleDownload.objects.filter(release=self.web_release).count())
        self.assertEqual(1, WebBundleReleaseDownloadsByDate.objects.get(
            release=self.web_release, when=self.today).count)


class AppStatsTimelineTestCase(DownloadFixtureMixin, TestCase):

    def setUp(self):
        self.create_fixtures()
        self.day = datetime.date(2026, 1, 15)

    def get_timeline(self, app_name):
        response = self.client.get('/download/stats/%s/timeline' % app_name)
        self.assertEqual(200, response.status_code)
        return json.loads(response.content)

    def test_desktop_timeline(self):
        ReleaseDownloadsByDate.objects.create(release=self.desktop_release, when=self.day, count=3)
        self.assertEqual({'3.0.0': [['2026-01-15', 3]]}, self.get_timeline('jarapp'))

    def test_service_timeline(self):
        ServiceReleaseDownloadsByDate.objects.create(release=self.service_release, when=self.day, count=4)
        ServiceReleaseDownloadsByDate.objects.create(release=None, when=self.day, count=4)
        self.assertEqual({'1.0.0': [['2026-01-15', 4]], '0.9.0': []},
                         self.get_timeline('svcapp'))

    def test_web_timeline(self):
        WebBundleReleaseDownloadsByDate.objects.create(release=self.web_release, when=self.day, count=5)
        self.assertEqual({'2.0.0': [['2026-01-15', 5]]}, self.get_timeline('webapp'))

    def test_timeline_reads_only_its_platforms_counts(self):
        # ids can collide across the release tables; each platform must read its own by-date model
        ReleaseDownloadsByDate.objects.create(release=self.desktop_release, when=self.day, count=7)
        self.assertEqual({'1.0.0': [], '0.9.0': []}, self.get_timeline('svcapp'))

    def test_unknown_app_is_404(self):
        self.assertEqual(404, self.client.get('/download/stats/nosuchapp/timeline').status_code)

    def test_inactive_app_is_404(self):
        self.service_app.active = False
        self.service_app.save()
        self.assertEqual(404, self.client.get('/download/stats/svcapp/timeline').status_code)


class DesktopInstallLiveServerTestCase(DownloadFixtureMixin, LiveServerTestCase):
    """The desktop install beacon end to end over HTTP: install calls, then the stats they feed."""

    def setUp(self):
        self.create_fixtures()
        self.today = datetime.date.today().isoformat()

    def http_get(self, path):
        # http.client never follows redirects, so the 302 to Cytoscape Web is observable
        server = urlparse(self.live_server_url)
        connection = http.client.HTTPConnection(server.hostname, server.port, timeout=10)
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            return response.status, response.getheader('Location'), response.read()
        finally:
            connection.close()

    def test_desktop_and_web_installs_reach_stats(self):
        status, location, body = self.http_get(self.install_url(self.service_app, '1.0.0', 'desktop'))
        self.assertEqual(204, status)
        self.assertIsNone(location)
        self.assertEqual(b'', body)

        status, location, _ = self.http_get(self.install_url(self.service_app, '1.0.0'))
        self.assertEqual(302, status)
        self.assertEqual(self.service_release.install_url, location)

        status, _, body = self.http_get('/download/stats/svcapp/timeline')
        self.assertEqual(200, status)
        self.assertEqual([[self.today, 2]], json.loads(body)['1.0.0'])

        status, _, body = self.http_get('/download/stats/timeline')
        self.assertEqual(200, status)
        self.assertIn([self.today, 2], json.loads(body)['Total'])

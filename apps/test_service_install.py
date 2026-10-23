"""
Browser tests of the service app page's "Install in Cytoscape Desktop" button (appstore#151).

Headless Chromium (Playwright) loads the real page from a live test server. Calls the page
makes to Cytoscape Desktop on 127.0.0.1:1234 are answered by FakeCyRest instead of a Desktop.
"""
import json
import os
import re
from urllib.parse import parse_qs, urlparse

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright

from apps.models import App, Platform, ServiceRelease
from download.models import ServiceDownload

CYREST = 'http://127.0.0.1:1234'

NOT_RUNNING = 'Start Cytoscape Desktop 3.10 or later, then reload this page.'
SERVICE_APP_MISSING = 'Desktop needs the Service App installed first to enable service app installation.'
UNREADABLE = "Couldn't read installed service apps from Cytoscape Desktop."


class FakeCyRest:
    """
    A fake of Cytoscape Desktop's CyREST, served to the browser through Playwright routing.

    It mocks only what the service app page calls:

    - ``GET /v1``, CyREST's answer that Desktop is running (and ``/v1/version``, which the
      page's js4cytoscape badge script asks for);
    - ``GET /v1/commands/serviceapps/list`` and ``.../serviceapps/install``, the commands that
      desktop-service-app adds to Desktop.

    Replies follow cyREST's GET command handling: the command's text result then ``Finished``,
    404 ``Error: no such namespace`` when desktop-service-app isn't installed, 500
    ``Failed: <message>`` when the command fails, and ``Access-Control-Allow-Origin: *``.

    The service app flow never calls Desktop's built-in ``apps install`` command (that is the
    jar app flow), so nothing here exercises or regression-tests the jar app install.
    """

    def __init__(self, running=True, service_app_installed=True, installed_apps=(),
                 list_reply=None, list_status=200, list_unreachable=False,
                 install_status=200, install_reply=None, install_hangs=False):
        self.running = running
        self.service_app_installed = service_app_installed
        self.installed_apps = list(installed_apps)
        self.list_reply = list_reply
        self.list_status = list_status
        self.list_unreachable = list_unreachable
        self.install_status = install_status
        self.install_reply = install_reply
        self.install_hangs = install_hangs
        self.requests = []
        self.stalled_routes = []

    def attach(self, page):
        page.route(CYREST + '/**', self.handle)

    def install_requests(self):
        return [r for r in self.requests if r.path == '/v1/commands/serviceapps/install']

    def handle(self, route, request):
        url = urlparse(request.url)
        self.requests.append(url)
        if not self.running:
            route.abort('connectionrefused')
            return
        if request.method == 'OPTIONS':
            self.reply(route, 204, '')
        elif url.path == '/v1':
            self.reply(route, 200, '{"availableApiVersions":["v1"]}', 'application/json')
        elif url.path == '/v1/version':
            self.reply(route, 200, '{"apiVersion":"v1","cytoscapeVersion":"3.10.3"}', 'application/json')
        elif url.path.startswith('/v1/commands/serviceapps/') and not self.service_app_installed:
            self.reply(route, 404, "Error: no such namespace: 'serviceapps'")
        elif url.path == '/v1/commands/serviceapps/list':
            if self.list_unreachable:
                route.abort('connectionrefused')  # Desktop quit after answering /v1
                return
            body = self.list_reply
            if body is None:
                body = json.dumps(self.installed_apps, separators=(',', ':')) + '\nFinished\n'
            self.reply(route, self.list_status, body)
        elif url.path == '/v1/commands/serviceapps/install':
            if self.install_hangs:
                self.stalled_routes.append(route)  # not answered, as when Desktop stalls
                return
            if self.install_status == 200:
                query = parse_qs(url.query)
                body = self.install_reply or 'installed %s %s\nFinished\n' % (query['name'][0], query['version'][0])
            else:
                body = self.install_reply
            self.reply(route, self.install_status, body)
        else:
            self.reply(route, 404, 'Not found')

    def release_stalled(self):
        for route in self.stalled_routes:
            route.abort()
        self.stalled_routes = []

    @staticmethod
    def reply(route, status, body, content_type='text/plain'):
        route.fulfill(status=status, body=body, content_type=content_type,
                      headers={'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Headers': 'origin, content-type, accept, authorization',
                               'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, HEAD'})


class ServiceInstallButtonTestCase(StaticLiveServerTestCase):

    ENDPOINT = 'https://service.example.org/hello'

    @classmethod
    def setUpClass(cls):
        # Playwright's sync API runs an event loop in this thread; let Django's ORM run beside it
        cls._async_unsafe = os.environ.get('DJANGO_ALLOW_ASYNC_UNSAFE')
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()
        if cls._async_unsafe is None:
            os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        else:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = cls._async_unsafe

    def setUp(self):
        self.app = App.objects.create(name='helloworldapp', fullname='Hello World App',
                                      platform=Platform.SERVICE, active=True, has_releases=True)
        self.release = ServiceRelease.objects.create(
            app=self.app, version='1.10', service_endpoint=self.ENDPOINT,
            metadata={'name': 'Hello World', 'version': '1.10'})
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.button = self.page.locator('#cy-app-install-btn')
        self.alerts = self.page.locator('#cy-alerts')
        self.cyrest = None

    def tearDown(self):
        if self.cyrest:
            self.cyrest.release_stalled()
        self.context.close()

    def open_page(self, cyrest):
        self.cyrest = cyrest
        cyrest.attach(self.page)
        self.page.goto(self.live_server_url + '/apps/helloworldapp', wait_until='domcontentloaded')

    def installed(self, version='1.10', url=ENDPOINT, name='Hello World'):
        return {'name': name, 'version': version, 'url': url, 'reachable': True}

    def expect_button(self, text, enabled, tooltip=None):
        """Button label and enabled state, and its tooltip: exactly ``tooltip``, or none at all."""
        expect(self.button.locator('h4')).to_have_text(text)
        if enabled:
            expect(self.button).not_to_have_class(re.compile(r'\bdisabled\b'))
        else:
            expect(self.button).to_have_class(re.compile(r'\bdisabled\b'))
        if tooltip is None:
            expect(self.button).not_to_have_attribute('title', re.compile(r'.*'))
        else:
            expect(self.button).to_have_attribute('title', tooltip)

    # --- page load states ---

    def test_desktop_not_running(self):
        self.open_page(FakeCyRest(running=False))
        self.expect_button('Install in Cytoscape Desktop', enabled=False, tooltip=NOT_RUNNING)
        expect(self.alerts.locator('a[href="/help/getstarted_app_install"]')).to_be_visible()
        expect(self.page.locator('#cy-app-url-latest')).to_have_value(self.ENDPOINT)

    def test_desktop_service_app_missing(self):
        self.open_page(FakeCyRest(service_app_installed=False))
        self.expect_button('Install in Cytoscape Desktop', enabled=False, tooltip=SERVICE_APP_MISSING)
        expect(self.button.locator('i')).to_have_class('icon-info-sign')
        link = self.alerts.locator('a[href="/apps/desktopserviceapp"]')
        expect(link).to_have_text('get the Desktop Service App')

    def test_not_installed_offers_install(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(name='Other App')]))
        self.expect_button('Install in Cytoscape Desktop', enabled=True)

    def test_identical_version_and_url_is_installed(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed()]))
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)

    def test_same_version_and_url_with_trailing_slash_is_installed(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(url=self.ENDPOINT + '/')]))
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)

    def test_older_version_offers_upgrade(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(version='1.9')]))
        self.expect_button('Upgrade in Cytoscape Desktop', enabled=True)

    def test_same_version_other_url_offers_upgrade(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(url='https://old.example.org/hello')]))
        self.expect_button('Upgrade in Cytoscape Desktop', enabled=True)

    def test_non_numeric_installed_version_offers_upgrade(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(version='1.10-beta')]))
        self.expect_button('Upgrade in Cytoscape Desktop', enabled=True)

    def test_newer_version_installed_offers_no_downgrade(self):
        self.open_page(FakeCyRest(installed_apps=[self.installed(version='2.0')]))
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)

    def test_unreadable_list(self):
        self.open_page(FakeCyRest(list_reply='Finished\n'))
        self.expect_button('Install in Cytoscape Desktop', enabled=False, tooltip=UNREADABLE)

    def test_list_command_error_is_unreadable(self):
        self.open_page(FakeCyRest(list_status=500, list_reply='Failed: registry unavailable\n'))
        self.expect_button('Install in Cytoscape Desktop', enabled=False, tooltip=UNREADABLE)

    def test_desktop_gone_before_list_is_not_running(self):
        cyrest = FakeCyRest(list_unreachable=True)
        self.open_page(cyrest)
        self.expect_button('Install in Cytoscape Desktop', enabled=False, tooltip=NOT_RUNNING)
        self.assertIn('/v1', [r.path for r in cyrest.requests])

    def test_html_wrapped_list_reply(self):
        listed = json.dumps([self.installed()], separators=(',', ':'))
        self.open_page(FakeCyRest(list_reply=(
            '<p style="color:green;margin-left:10px;">' + listed + '</p>\n'
            '<p style="color:black;margin-left:10px;">Finished</p>\n')))
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)

    # --- clicking Install / Upgrade ---

    def test_install_calls_serviceapps_install_and_counts(self):
        cyrest = FakeCyRest()
        self.open_page(cyrest)
        self.expect_button('Install in Cytoscape Desktop', enabled=True)
        with self.page.expect_response(re.compile(r'/download/install/helloworldapp/1\.10\?client=desktop$')) as beacon:
            self.button.click()
        self.assertEqual(204, beacon.value.status)
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)
        expect(self.alerts.locator('.alert-success')).to_contain_text('Hello World has been installed in Cytoscape Desktop!')

        [install] = cyrest.install_requests()
        self.assertEqual({'name': ['Hello World'], 'version': ['1.10'], 'url': [self.ENDPOINT]},
                         parse_qs(install.query))
        self.assertIn('url=https%3A%2F%2Fservice.example.org%2Fhello', install.query)
        self.assertEqual(1, ServiceDownload.objects.filter(release=self.release).count())

    def test_upgrade_ends_installed(self):
        cyrest = FakeCyRest(installed_apps=[self.installed(version='1.9')])
        self.open_page(cyrest)
        self.expect_button('Upgrade in Cytoscape Desktop', enabled=True)
        with self.page.expect_response(re.compile(r'\?client=desktop$')):
            self.button.click()
        self.expect_button('Installed in Cytoscape Desktop', enabled=False)
        self.assertEqual(1, len(cyrest.install_requests()))

    def test_failed_install_shows_message_and_does_not_count(self):
        message = ("Failed: the service at https://service.example.org/hello reports name 'Hello World'"
                   " version '1.9', not name 'Hello World' version '1.10'")
        self.open_page(FakeCyRest(install_status=500, install_reply=message))
        beacons = []
        self.page.on('request', lambda r: beacons.append(r.url) if 'client=desktop' in r.url else None)
        self.button.click()
        expect(self.alerts.locator('.alert-error')).to_contain_text(message)
        self.expect_button('Install in Cytoscape Desktop', enabled=True)
        self.assertEqual([], beacons)
        self.assertEqual(0, ServiceDownload.objects.count())

    def test_install_times_out_after_10_seconds(self):
        self.page.clock.install()
        self.open_page(FakeCyRest(install_hangs=True))
        self.expect_button('Install in Cytoscape Desktop', enabled=True)
        self.button.click()
        self.expect_button('Installing...', enabled=False)
        expect(self.button.locator('i')).to_have_class(re.compile(r'\bcy-spin\b'))
        self.page.clock.fast_forward(10001)
        expect(self.alerts.locator('.alert-error')).to_contain_text('Cytoscape Desktop did not answer within 10 seconds')
        self.expect_button('Install in Cytoscape Desktop', enabled=True)
        self.assertEqual(0, ServiceDownload.objects.count())

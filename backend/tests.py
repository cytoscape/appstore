"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import json
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import TestCase
from apps.models import App
from apps.models import Release


class BackendViewsTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()

    def tearDown(self):
        App.objects.all().delete()

    def test_all_apps_no_apps(self):
        response = self.client.get('/backend/all_apps')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_all_apps_one_app_not_active(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp')
        appobj.save()
        response = self.client.get('/backend/all_apps')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_all_apps_one_app_active_no_releases(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        response = self.client.get('/backend/all_apps')
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_all_apps_one_app_active_with_releases(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        uploaded = SimpleUploadedFile('my.jar',
                                      b'hello',
                                      content_type='text/plain')
        appobj = App.objects.get(name='myapp')
        myrel = Release.objects.create(app=appobj,
                                       version='1.0',
                                       release_file=uploaded)
        myrel.save()
        appobj.update_has_releases()
        appobj.save()
        response = self.client.get('/backend/all_apps')
        self.assertEqual(200, response.status_code)
        app_json = json.loads(response.content)
        self.assertEqual(1, len(app_json))
        self.assertEqual('MyApp', app_json[0]['fullname'])
        self.assertEqual(None, app_json[0]['description'])
        self.assertEqual(appobj.icon_url, app_json[0]['icon_url'])
        self.assertEqual(appobj.page_url, app_json[0]['page_url'])
        self.assertEqual(0, app_json[0]['downloads'])
        self.assertEqual(1, len(app_json[0]['releases']))
        # TODO add checks on rest of the json document

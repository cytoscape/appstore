"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import datetime
import io
import json
import os
import shutil
import zipfile
import tempfile
import random
import re
from html.parser import HTMLParser
from PIL import Image, ImageDraw

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.template import Context, Template
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from django.test import TestCase
from apps.models import App
from apps.models import Author
from apps.models import OrderedAuthor
from apps.models import Screenshot
from apps.models import ReleaseAPI
from apps.models import Tag
from apps import models as apps_models
from apps import views as apps_views
from apps.models import Release
from apps.models import ServiceRelease
from apps.models import WebBundleRelease
from apps.models import Platform
from apps.models import AppPlatformContent
from apps.views import _AppPageEditConfig
from apps.templatetags import app_buttons
from submit_app.models import ServiceAppPending
from submit_app.models import WebBundlePending
from submit_app.models import AppPending
from submit_app.models import WebUrlPending

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


def clear_media_root():
    shutil.rmtree(settings.MEDIA_ROOT)
    os.makedirs(settings.MEDIA_ROOT, mode=0o755)


class AuthorTestCase(TestCase):

    def setUp(self):
        Author.objects.all().delete()
        Author.objects.create(name='Bob Smith',
                              institution='U of U')
        Author.objects.create(name='Joe Joe')

        # make an empty author
        Author.objects.create()

    def tearDown(self):
        Author.objects.all().delete()

    def test_str_for_author_objects(self):
        bob = Author.objects.get(name='Bob Smith')
        self.assertEqual('Bob Smith (U of U)', str(bob))

        joe = Author.objects.get(name='Joe Joe')
        self.assertEqual('Joe Joe', str(joe))

        empty = Author.objects.get(name='')
        self.assertEqual('', str(empty))


class TagTestCase(TestCase):

    def setUp(self):
        Tag.objects.all().delete()

    def tearDown(self):
        Tag.objects.all().delete()

    def test_only_one_tag(self):
        Tag.objects.create(name='foo')
        first = Tag.objects.get(name='foo')
        self.assertEqual('foo', str(first))
        self.assertEqual(0, first.count)
        self.assertEqual(0, first.count)

    def test_ordering(self):
        Tag.objects.create(name='beta')
        Tag.objects.create(name='alpha')
        Tag.objects.create(name='charlie')

        results = Tag.objects.all()
        self.assertEqual(3, len(results))
        self.assertEqual('alpha', results[0].name)
        self.assertEqual('beta', results[1].name)
        self.assertEqual('charlie', results[2].name)


class AppTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        Author.objects.all().delete()
        OrderedAuthor.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        Author.objects.all().delete()
        OrderedAuthor.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def test_str_for_app(self):
        appobj = App.objects.create(name='foo')
        self.assertEqual(appobj.name, str(appobj))

    def test_is_editor(self):
        App.objects.create(name='foo')
        appobj = App.objects.get(name='foo')

        self.assertEqual(False, appobj.is_editor(None))

        # check that staff user can edit
        User.objects.create_user('staffuser', is_staff=True,
                                 is_superuser=False)
        staffuser = User.objects.get(username='staffuser')
        self.assertEqual(True, appobj.is_editor(staffuser))

        # check that super user can edit
        User.objects.create_user('superuser', is_staff=False,
                                 is_superuser=True)
        superuser = User.objects.get(username='superuser')
        self.assertEqual(True, appobj.is_editor(superuser))

        # check that user is NOT in editors
        someuser = User.objects.create_user('someuser',
                                            is_staff=False,
                                            is_superuser=False)
        self.assertEqual(False, appobj.is_editor(someuser))

        # add some editors and check where user is there
        euser = User.objects.create_user('euser',
                                         is_staff=False,
                                         is_superuser=False,
                                         email='euser@foo.com')
        euser.save()
        euser = User.objects.get(username='euser')
        blah_app_obj = App.objects.create(name='blah',
                                          fullname='blah full')
        blah_app_obj.save()
        blah_app_obj.editors.add(euser)
        blah_app_obj = App.objects.get(name='blah')
        self.assertEqual(True, blah_app_obj.is_editor(euser))

    def test_camelcase(self):
        appobj = App.objects.create(name='x', fullname='x')
        self.assertEqual('x', appobj.camelcase())

        appobj = App.objects.create(name='xyz', fullname='xYz')
        self.assertEqual('x Yz', appobj.camelcase())

        appobj = App.objects.create(name='disgenet', fullname='DisGeNet')
        self.assertEqual('Dis Ge Net', appobj.camelcase())

        appobj = App.objects.create(name='genemania', fullname='GeneMANIA')
        self.assertEqual('Gene MANIA', appobj.camelcase())

    def test_stars_percentage(self):
        appobj = App.objects.create(name='x', fullname='x')
        self.assertEqual(0, appobj.stars_percentage)

        appobj.stars = 4
        appobj.votes = 2
        self.assertAlmostEqual(40.0, appobj.stars_percentage)

        appobj.stars = 5
        appobj.votes = 1
        self.assertAlmostEqual(100.0, appobj.stars_percentage)

    def test_icon_url(self):
        appobj = App.objects.create(name='x', fullname='x')
        self.assertEqual(apps_models.GENERIC_ICON_URL,
                         appobj.icon_url)

        uploaded = SimpleUploadedFile('small.gif', SMALL_GIF,
                                      content_type='image/gif')

        appobj = App.objects.create(name='y', fullname='y', icon=uploaded)

        self.assertTrue(os.path.join(settings.MEDIA_URL, 'y', 'small') in
                        appobj.icon_url)

    def test_ordered_authors(self):
        appobj = App.objects.create(name='x', fullname='x')
        appobj.save()
        appobj = App.objects.get(name='x')

        # try with no ordered authors
        res = list(appobj.ordered_authors)
        self.assertEqual([], res)

        # try with one ordered author
        author_one = Author.objects.create(name='Bob Smith',
                                          institution='U of U')
        author_one.save()
        author_one = Author.objects.get(name='Bob Smith')

        o_author_one = OrderedAuthor.objects.create(author=author_one, app=appobj,
                                                    author_order=1)
        o_author_one.save()

        # quick test __str__() is working
        self.assertEqual('1: x by Bob Smith', str(o_author_one))

        res = list(appobj.ordered_authors)
        self.assertEqual(1, len(res))
        self.assertEqual('Bob Smith', res[0].name)

        # try with two ordered authors
        author_two = Author.objects.create(name='Aaron Aaron',
                                           institution='U of U')
        author_two.save()
        author_two = Author.objects.get(name='Aaron Aaron')

        o_author_two = OrderedAuthor.objects.create(author=author_two, app=appobj, author_order=0)
        o_author_two.save()
        res = list(appobj.ordered_authors)
        self.assertEqual(2, len(res))
        self.assertEqual('Aaron Aaron', res[0].name)
        self.assertEqual('Bob Smith', res[1].name)


class ReleaseTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        Release.objects.all().delete()
        ReleaseTestCase.APPOBJ = App.objects.create(name='myapp', fullname='MyApp')
        ReleaseTestCase.APPOBJ.save()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        clear_media_root()

    FILE_CONTENT = b'hello'

    def test_app_str_and_release_file_url(self):
        appobj = App.objects.get(name='myapp')
        uploaded = SimpleUploadedFile('my.jar',
                                      ReleaseTestCase.FILE_CONTENT,
                                      content_type='text/plain')
        myrel = Release.objects.create(app=appobj,
                                       version='1.0',
                                       release_file=uploaded)
        self.assertEqual('MyApp 1.0', str(myrel))

        self.assertTrue('/myapp/releases/1.0/my' in myrel.release_file_url)

    def test_version_tuple(self):
        uploaded = SimpleUploadedFile('my.jar',
                                      ReleaseTestCase.FILE_CONTENT,
                                      content_type='text/plain')
        appobj = App.objects.get(name='myapp')
        myrel = Release.objects.create(app=appobj,
                                       version='1.0',
                                       release_file=uploaded)
        self.assertEqual((1, 0, None, None), myrel.version_tuple)

        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='2.1.3',
                                       release_file=uploaded)
        self.assertEqual((2, 1, 3, None), myrel.version_tuple)

        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='2.1.4.',
                                       release_file=uploaded)
        self.assertEqual(None, myrel.version_tuple)

        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='3.4.6.foo',
                                       release_file=uploaded)
        self.assertEqual((3, 4, 6, 'foo'), myrel.version_tuple)

        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='3.4.6.13',
                                       release_file=uploaded)
        self.assertEqual((3, 4, 6, '13'), myrel.version_tuple)

    def test_calc_checksum(self):
        uploaded = SimpleUploadedFile('my.jar',
                                      ReleaseTestCase.FILE_CONTENT,
                                      content_type='text/plain')
        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='1.0',
                                       release_file=uploaded)

        myrel.calc_checksum()
        self.assertEqual('sha512:9b71d224bd62f3785d96d46ad'
                         '3ea3d73319bfbc2890caadae2dff7251'
                         '9673ca72323c3d99ba5c11d7c7acc6e1'
                         '4b8c5da0c4663475c2e5c3adef46f73b'
                         'cdec043', myrel.hexchecksum)

    def test_delete_files(self):
        uploaded = SimpleUploadedFile('my.jar',
                                      ReleaseTestCase.FILE_CONTENT,
                                      content_type='text/plain')
        myrel = Release.objects.create(app=ReleaseTestCase.APPOBJ,
                                       version='1.0',
                                       release_file=uploaded)

        self.assertNotEqual(None, myrel.release_file)
        myrel.delete_files()

        self.assertEqual(None, myrel.release_file)


class ScreenshotTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        appobj = App.objects.create(name='myapp', fullname='MyApp')
        appobj.save()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        Screenshot.objects.all().delete()
        clear_media_root()

    def test_str(self):
        appobj = App.objects.get(name='myapp')

        screenshot_file = SimpleUploadedFile('myimage.png',
                                             b'hello',
                                             content_type='image/png')

        thumbnail_file = SimpleUploadedFile('mythumb.png',
                                             b'bye',
                                             content_type='image/png')

        s_shot = Screenshot.objects.create(app=appobj,
                                           screenshot=screenshot_file,
                                           thumbnail=thumbnail_file)
        self.assertEqual('MyApp - 1', str(s_shot))
        s_shot.save()
        s_shot = Screenshot.objects.get(app=appobj)
        self.assertEqual('MyApp - 1', str(s_shot))

        self.assertTrue(os.path.join(settings.MEDIA_URL,
                                     'myapp',
                                     'screenshots') in s_shot.screenshot.url)
        self.assertTrue(os.path.join(settings.MEDIA_URL,
                                     'myapp',
                                     'thumbnails') in s_shot.thumbnail.url)


class ReleaseAPITestCase(TestCase):

    def setUp(self):
        clear_media_root()
        App.objects.all().delete()
        Release.objects.all().delete()
        appobj = App.objects.create(name='myapp', fullname='MyApp')
        appobj.save()
        uploaded = SimpleUploadedFile('my.jar',
                                      b'hello',
                                      content_type='text/plain')
        myrel = Release.objects.create(app=appobj,
                                       version='1.0',
                                       release_file=uploaded,
                                       active=True)
        myrel.save()

    def tearDown(self):
        App.objects.all().delete()
        Release.objects.all().delete()
        ReleaseAPI.objects.all().delete()
        clear_media_root()

    def test_extract_javadocs(self):
        appobj = App.objects.get(name='myapp')
        myrel = appobj.releases[0]
        javajar = SimpleUploadedFile('my.jar',
                                      b'hello',
                                      content_type='application/octet-stream')
        pom = SimpleUploadedFile('my.jar',
                                      b'<x>hi</x>',
                                      content_type='text/xml')
        repapi = ReleaseAPI.objects.create(release=myrel,
                                           javadocs_jar_file=javajar,
                                           pom_xml_file=pom)
        repapi.save()
        self.assertEqual('MyApp 1.0', str(repapi))

    def test_extract_javadocs_jar_valid_zip(self):
        temp_dir = tempfile.mkdtemp()
        try:
            temp_zip = os.path.join(temp_dir, 'foo.jar')
            zf = zipfile.ZipFile(temp_zip, mode='w')
            zf.writestr('hi.xml', 'somedata')
            zf.close()
            with open(temp_zip, 'rb') as f:
                zipdata = f.read()
            javadocjar = SimpleUploadedFile('foo.jar',
                                            zipdata,
                                            content_type='application/octet-stream')

            appobj = App.objects.get(name='myapp')
            myrel = appobj.releases[0]
            repapi = ReleaseAPI.objects.create(release=myrel,
                                               javadocs_jar_file=javadocjar)
            repapi.save()
            repapi.extract_javadocs_jar()

            extract_dir = os.path.join(settings.MEDIA_ROOT, 'myapp',
                                       'releases', '1.0', 'foo.jar-extracted')
            jfile = os.path.join(settings.MEDIA_ROOT, 'myapp',
                                 'releases', '1.0', 'foo.jar')
            self.assertTrue(os.path.isfile(jfile))

            self.assertTrue(os.path.isdir(extract_dir))
            self.assertTrue(os.path.isfile(os.path.join(extract_dir, 'hi.xml')))

            # now lets delete it
            repapi.delete_files()
            self.assertFalse(os.path.isdir(extract_dir))
            jfile = os.path.join(settings.MEDIA_ROOT, 'myapp',
                                       'releases', '1.0', 'foo.jar')
            self.assertFalse(os.path.isfile(jfile))

        finally:
            shutil.rmtree(temp_dir)

    def test_extract_javadocs_jar_invalid_zip(self):

        javadocjar = SimpleUploadedFile('foo.jar',
                                        b'invalid zip data',
                                        content_type='application/octet-stream')

        appobj = App.objects.get(name='myapp')
        myrel = appobj.releases[0]
        repapi = ReleaseAPI.objects.create(release=myrel,
                                           javadocs_jar_file=javadocjar)
        repapi.save()
        repapi.extract_javadocs_jar()

        extract_dir = os.path.join(settings.MEDIA_ROOT, 'myapp',
                                   'releases', '1.0', 'foo.jar-extracted')
        self.assertTrue(os.path.isdir(extract_dir))
        self.assertEqual([], os.listdir(extract_dir))


class ViewsAppPageTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        Release.objects.all().delete()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        Release.objects.all().delete()
        clear_media_root()

    def test_legacy_app_download_button_uses_release_download_url(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True, has_releases=True)
        uploaded = SimpleUploadedFile('my.jar',
                                      ReleaseTestCase.FILE_CONTENT,
                                      content_type='text/plain')
        Release.objects.create(app=appobj,
                               version='1.0',
                               release_file=uploaded,
                               active=True)

        response = self.client.get('/apps/myapp')

        self.assertEqual(200, response.status_code)
        content = str(response.content, 'utf-8')
        self.assertIn('"/download/myapp/1.0"', content)
        self.assertNotIn('AppPage.setup_install("myapp",\n\t"MyApp",\n\t"1.0"',
                         content)


class ViewsAppPageEditTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def test_not_editor(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=False)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        response = self.client.post('/apps/myapp/edit',
                                    follow=True)
        self.assertEqual(403, response.status_code)

    def test_no_action_specified(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        response = self.client.post('/apps/myapp/edit',
                                    follow=True)

        self.assertEqual(400, response.status_code)
        self.assertEqual(b'no action specified', response.content)

    def test_invalid_action(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'nonexistantaction'},
                                    follow=True)

        self.assertEqual(400, response.status_code)
        self.assertTrue('action "nonexistantaction" invalid--must be: ' in
                        str(response.content, 'utf-8'))

    def test_upload_screenshot_no_file(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)
        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'upload_screenshot'},
                                    follow=True)

        self.assertEqual(400, response.status_code)
        self.assertEqual(b'no file submitted', response.content)

    def test_upload_screenshot_valid_file(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True)
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        img = Image.new('RGB', (400, 300))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        myimg = SimpleUploadedFile('pic.png', img_bytes.getvalue(),
                                   content_type='image/png')

        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'upload_screenshot',
                                     'file': myimg},
                                    follow=True)

        self.assertEqual(200, response.status_code)
        s_shot = Screenshot.objects.get(app=appobj)
        self.assertTrue(os.path.isfile(s_shot.screenshot.path))
        img = Image.open(s_shot.screenshot.path)
        self.assertEqual((400, 300), img.size)

        self.assertTrue(os.path.isfile(s_shot.thumbnail.path))
        img = Image.open(s_shot.thumbnail.path)
        self.assertEqual((200, 150), img.size)

    def test_upload_screenshot_too_large(self):
        orig_max_size = _AppPageEditConfig.max_img_size_b
        _AppPageEditConfig.max_img_size_b = 50
        try:
            appobj = App.objects.create(name='myapp', fullname='MyApp',
                                        active=True)
            appobj.save()
            User.objects.create_user(username='bob', password='secret',
                                     is_superuser=True)
            res = self.client.login(username='bob', password='secret')
            self.assertTrue(res)

            img = Image.new('RGB', (800, 600))
            draw = ImageDraw.Draw(img)
            for x in range(0, 800):
                draw.line([(x, 0), (x, 600)],
                          fill=(random.randint(0, 255),
                                random.randint(0, 255),
                                random.randint(0, 255)))
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            myimg = SimpleUploadedFile('pic.png', img_bytes.getvalue(),
                                       content_type='image/png')

            response = self.client.post('/apps/myapp/edit',
                                        {'action': 'upload_screenshot',
                                         'file': myimg},
                                        follow=True)

            self.assertEqual(400, response.status_code)
            self.assertTrue('image file is ' in
                            str(response.content, 'utf-8'))
            self.assertTrue('but can be at most 50 bytes' in
                            str(response.content, 'utf-8'))
        finally:
            _AppPageEditConfig.max_img_size_b = orig_max_size

    def test_check_editor_no_editor_email_specified(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True, email='bob@bob.com')
        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'check_editor'},
                                    follow=True, **header)

        self.assertEqual(400, response.status_code)
        self.assertEqual('no editor_email specified',
                         str(response.content, 'utf-8'))

    def test_check_editor_no_matching_editor(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True, email='bob@bob.com')

        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'check_editor',
                                     'editor_email': 'asdf@joe.com'},
                                    follow=True, **header)

        self.assertEqual(200, response.status_code)
        self.assertEqual(False, response.json())

    def test_check_editor_multiple_matching_editors(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        User.objects.create_user(username='bob', password='secret',
                                 is_superuser=True, email='bob@bob.com')

        res = self.client.login(username='bob', password='secret')
        self.assertTrue(res)

        User.objects.create_user(username='xxx', password='secret',
                                 is_superuser=False, email='new@new.com')
        User.objects.create_user(username='yyy', password='secret',
                                 is_superuser=False, email='new@new.com')

        # this header lines tells the app the request is
        # an ajax request cause the code makes the call
        # request.is_ajax()
        # see:
        # https://docs.djangoproject.com/en/3.0/ref/
        #        request-response/#django.http.HttpRequest.is_ajax
        header = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        response = self.client.post('/apps/myapp/edit',
                                    {'action': 'check_editor',
                                     'editor_email': 'new@new.com'},
                                    follow=True, **header)

        self.assertEqual(200, response.status_code)
        self.assertEqual('yyy', response.json())


class AppButtonsTestCase(TestCase):

    def setUp(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def tearDown(self):
        App.objects.all().delete()
        User.objects.all().delete()
        clear_media_root()

    def test_app_button_by_name_where_app_not_found(self):
        res = app_buttons.app_button_by_name('noexist')
        self.assertEqual({}, res)

    def test_app_button_by_name_found_app(self):
        appobj = App.objects.create(name='myapp', fullname='MyApp',
                                    active=True)
        appobj.save()
        res = app_buttons.app_button_by_name('myapp')
        self.assertEqual('myapp', res['app'].name)


class ServiceReleaseOrderingTestCase(TestCase):

    def setUp(self):
        self.app = App.objects.create(name='svcapp', fullname='Service App',
                                      active=True, has_releases=True)
        self.base_time = datetime.datetime(2026, 1, 1)

    def make_release(self, version, days_old, active=True):
        release = ServiceRelease.objects.create(
            app=self.app, version=version, active=active,
            service_endpoint='https://service.example.org/v' + version)
        # created is auto_now_add, so set it after the insert
        ServiceRelease.objects.filter(pk=release.pk).update(
            created=self.base_time - datetime.timedelta(days=days_old))
        return release

    def versions(self):
        return [release.version for release in self.app.servicereleases_by_version]

    def test_service_version_key(self):
        key = apps_models._service_version_key
        self.assertGreater(key('1.10'), key('1.9'))
        self.assertGreater(key('2.0.1'), key('2.0'))
        self.assertEqual(key('1.0'), key('1.0.0'))
        self.assertEqual((1, 2, 3), key('1.2.3'))
        for unparseable in ('abc', '1.x', '1.0-beta', '', None):
            self.assertIsNone(key(unparseable), unparseable)

    def test_latest_version_first_regardless_of_created(self):
        self.make_release('1.10', days_old=5)
        self.make_release('1.9', days_old=1)
        self.make_release('1.2.3', days_old=0)
        self.assertEqual(['1.10', '1.9', '1.2.3'], self.versions())

    def test_unparseable_version_sorts_last(self):
        self.make_release('custom', days_old=0)
        self.make_release('0.1', days_old=9)
        self.assertEqual(['0.1', 'custom'], self.versions())

    def test_equal_versions_tie_broken_by_newest_created(self):
        self.make_release('1.0', days_old=3)
        self.make_release('1.0.0', days_old=1)
        self.assertEqual(['1.0.0', '1.0'], self.versions())

    def test_inactive_releases_excluded(self):
        self.make_release('2.0', days_old=0, active=False)
        self.make_release('1.0', days_old=1)
        self.assertEqual(['1.0'], self.versions())

    def test_releases_for_display_by_platform(self):
        self.make_release('1.9', days_old=0)
        self.make_release('1.10', days_old=1)
        self.assertEqual(['1.10', '1.9'], [r.version for r in self.app.releases_for_display('service')])
        desktop_app = App.objects.create(name='jarapp', fullname='Jar App', active=True)
        self.assertQuerySetEqual(desktop_app.get_releases('desktop'), desktop_app.releases_for_display('desktop'))

    def test_resubmitted_old_version_does_not_become_latest(self):
        self.make_release('1.10', days_old=1)
        self.make_release('1.9', days_old=5)
        submitter = User.objects.create_user('submitter', 'submitter@example.org', 'secret')
        pending = ServiceAppPending.objects.create(
            submitter=submitter, fullname='Service App', version='1.9',
            service_endpoint='https://service.example.org/v1.9-again')
        pending.make_service_release(self.app)
        # the resubmission resets created to now, newer than 1.10
        self.assertGreater(ServiceRelease.objects.get(app=self.app, version='1.9').created,
                           ServiceRelease.objects.get(app=self.app, version='1.10').created)
        self.assertEqual(['1.10', '1.9'], self.versions())

    def test_edit_page_lists_releases_by_version(self):
        self.make_release('1.10', days_old=5)
        self.make_release('1.9', days_old=1)
        editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.app.editors.add(editor)
        self.client.login(username='editor', password='secret')
        response = self.client.get('/apps/svcapp/edit')
        self.assertEqual(200, response.status_code)
        self.assertEqual(('service', ['1.10', '1.9']),
                         (response.context['selected_platform'], [r.version for r in response.context['selected_releases']]))

    def test_service_page_works_with_web_and_desktop(self):
        self.make_release('1.10', days_old=1)
        self.make_release('1.9', days_old=2)
        html = self.client.get('/apps/svcapp').content.decode()
        works_with = ('Cytoscape Web</a>, or <a href="http://www.cytoscape.org" target="_blank">Cytoscape Desktop</a> 3.10+'
                      ' with the <a href="/apps/desktopserviceapp">Desktop Service App</a> installed')
        # the side panel plus one line per release in the Releases tab
        self.assertEqual(3, html.count(works_with))
        self.assertNotIn('<strong>Works with</strong> Cytoscape\n', html)

    def test_service_page_uses_latest_version(self):
        self.make_release('1.10', days_old=5)
        self.make_release('1.9', days_old=1)
        response = self.client.get('/apps/svcapp')
        self.assertEqual(200, response.status_code)
        self.assertEqual('1.10', response.context['service_latest_release'].version)
        releases_tab = response.content.decode().split('id="cy-app-releases-tab"', 1)[1]
        self.assertLess(releases_tab.index('https://service.example.org/v1.10'),
                        releases_tab.index('https://service.example.org/v1.9'))


class SeedIntegrationDataTestCase(TestCase):
    """seed_integration_data, which the integration-test container runs before serving."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        media = os.path.join(self.tmp, 'media')
        storages = dict(settings.STORAGES)
        storages['webbundles'] = {**storages['webbundles'],
                                  'OPTIONS': {**storages['webbundles']['OPTIONS'],
                                              'location': os.path.join(media, 'webbundles')}}
        self.overrides = self.settings(INTEGRATION_SEED_ENABLED=True, BUILD_DIR=self.tmp,
                                       MEDIA_ROOT=media, STORAGES=storages,
                                       CDN_BASE_URL='http://localhost:8080/web/')
        self.overrides.enable()

    def tearDown(self):
        self.overrides.disable()
        shutil.rmtree(self.tmp)

    def seed(self):
        call_command('seed_integration_data', stdout=io.StringIO())
        with open(os.path.join(self.tmp, 'it_sessions.json')) as f:
            return json.load(f)

    def signed_in_user(self, session_key):
        self.client.cookies['sessionid'] = session_key
        return self.client.get('/apps/itdesktop').wsgi_request.user

    def test_seeds_users_apps_and_releases(self):
        self.seed()
        self.assertTrue(User.objects.get(username='it-admin').is_staff)
        self.assertFalse(User.objects.get(username='it-editor').is_staff)
        self.assertFalse(User.objects.get(username='it-other').is_staff)

        apps = {app.name: app for app in App.objects.all()}
        self.assertEqual({'itdesktop', 'itweb', 'itservice', 'itmulti', 'itedit', 'itlicensed', 'itretired', 'itlegacy',
                          'itcy2', 'itswitch', 'itcontent'},
                         set(apps))
        self.assertTrue(apps['itlicensed'].license_confirm)
        self.assertEqual([], apps['itretired'].platforms)
        self.assertEqual([Platform.DESKTOP, Platform.WEB, Platform.SERVICE], apps['itmulti'].platforms)
        self.assertEqual(['1.0'], [r.version for r in apps['itdesktop'].releases])
        self.assertTrue(os.path.exists(apps['itdesktop'].releases[0].release_file.path))
        self.assertEqual(['1.0'], [r.version for r in apps['itweb'].webbundlereleases])
        self.assertEqual(['1.0'], [r.version for r in apps['itservice'].servicereleases])
        self.assertFalse(apps['itlegacy'].has_releases)
        self.assertTrue(apps['itlegacy'].cy_2x_plugin_download)
        for name in apps:
            self.assertEqual(['it-editor'], [u.username for u in apps[name].editors.all()])

        # IT Multi's own content and its web content; its service version shows the app's
        multi = apps['itmulti']
        self.assertEqual(('IT Multi for the desktop', ['it-desktop'], ['Desktop Author']),
                         (multi.content(Platform.DESKTOP).details, [t.fullname for t in multi.content(Platform.DESKTOP).tags],
                          [a.name for a in multi.content(Platform.DESKTOP).authors]))
        web = multi.content(Platform.WEB)
        self.assertEqual(('IT Multi in the browser', 'IT Multi for the web', ['it-shared-category', 'it-web-only'],
                          ['Web Author']),
                         (web.description, web.details, sorted(t.fullname for t in web.tags), [a.name for a in web.authors]))
        # on two apps, and on IT Multi only through its web content
        self.assertEqual(3, Tag.objects.get(name='itsharedcategory').count)
        self.assertTrue(os.path.exists(web.screenshots.get().thumbnail.path))
        self.assertEqual('IT Multi for the desktop', multi.content(Platform.SERVICE).details)
        self.assertEqual('https://example.org/it-licensed-service-license',
                         apps['itlicensed'].content(Platform.SERVICE).license_text)
        self.assertEqual([Platform.DESKTOP, Platform.WEB], apps['itcy2'].platforms)
        self.assertTrue(apps['itcy2'].cy_2x_plugin_download)

        pending = WebBundlePending.objects.get()
        self.assertEqual(('IT Desktop', '1.0', 'it-editor'), (pending.fullname, pending.version, pending.submitter.username))
        self.assertTrue(pending.is_new_platform)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, 'media', 'webbundles', pending.bundle_path, 'remoteEntry.js')))
        self.assertTrue(AppPending.objects.get(fullname='IT Brand New').is_new_app)
        self.assertEqual('not_editor', AppPending.objects.get(fullname='IT Web').identity.outcome.value)
        self.assertTrue(ServiceAppPending.objects.get(fullname='IT Desktop').is_new_platform)
        self.assertEqual(['IT Url App'], [p.fullname for p in WebUrlPending.objects.all()])

    def test_sessions_sign_in_each_user(self):
        sessions = self.seed()
        for role, username in (('admin', 'it-admin'), ('editor', 'it-editor'), ('other', 'it-other')):
            self.assertEqual(username, self.signed_in_user(sessions[role]).username)

    def test_reseeding_replaces_the_data(self):
        self.seed()
        sessions = self.seed()
        self.assertEqual(11, App.objects.count())
        self.assertEqual(2, AppPlatformContent.objects.count())
        self.assertEqual(1, WebBundlePending.objects.count())
        self.assertEqual(1, ServiceAppPending.objects.count())
        self.assertEqual(3, User.objects.filter(username__startswith='it-').count())
        self.assertEqual('it-editor', self.signed_in_user(sessions['editor']).username)

    def test_refuses_unless_enabled(self):
        with self.settings(INTEGRATION_SEED_ENABLED=False):
            with self.assertRaises(CommandError):
                call_command('seed_integration_data', stdout=io.StringIO())


class AppPlatformsTestCase(TestCase):
    """An app is on a platform when it has an active release of that platform's type."""

    def setUp(self):
        self.app = App.objects.create(name='multi', fullname='Multi', active=True)

    def add_desktop(self, version='1.0', active=True):
        return Release.objects.create(app=self.app, version=version, works_with='3.10', active=active)

    def add_web(self, version='1.0', active=True):
        return WebBundleRelease.objects.create(app=self.app, version=version, active=active, bundle_hash='0')

    def add_service(self, version='1.0', active=True):
        return ServiceRelease.objects.create(app=self.app, version=version, active=active,
                                             service_endpoint='https://service.example.org/multi')

    def loaded(self):
        return App.objects.get(pk=self.app.pk)

    def flags(self, app):
        return app.has_desktop, app.has_web, app.has_service

    def test_no_releases_means_no_platforms(self):
        app = self.loaded()
        self.assertEqual((False, False, False), self.flags(app))
        self.assertEqual([], app.platforms)
        self.assertIsNone(app.primary_platform)

    def test_each_release_type_sets_its_platform(self):
        for add, flags in ((self.add_web, (False, True, False)),
                           (self.add_service, (False, True, True)),
                           (self.add_desktop, (True, True, True))):
            add()
            self.assertEqual(flags, self.flags(self.loaded()))

    def test_inactive_releases_do_not_count(self):
        self.add_desktop(active=False)
        self.add_web(active=False)
        self.add_service(active=False)
        self.assertEqual((False, False, False), self.flags(self.loaded()))

    def test_flags_without_annotations(self):
        self.add_web()
        self.add_service()
        unannotated = App._base_manager.get(pk=self.app.pk)
        self.assertFalse(hasattr(unannotated, 'platform_web'))
        self.assertEqual((False, True, True), self.flags(unannotated))
        release = ServiceRelease.objects.get(app=self.app)
        self.assertEqual((False, True, True), self.flags(release.app))

    def test_platforms_in_display_order_and_primary(self):
        self.add_service()
        self.add_web()
        app = self.loaded()
        self.assertEqual([Platform.WEB, Platform.SERVICE], app.platforms)
        self.assertEqual(Platform.WEB, app.primary_platform)
        self.assertTrue(app.has_platform('service'))
        self.assertFalse(app.has_platform('desktop'))
        self.add_desktop()
        self.assertEqual(Platform.DESKTOP, self.loaded().primary_platform)

    def test_get_releases_per_platform(self):
        desktop = self.add_desktop()
        web = self.add_web()
        service = self.add_service()
        self.add_service(version='0.9', active=False)
        app = self.loaded()
        self.assertEqual([desktop], list(app.get_releases('desktop')))
        self.assertEqual([web], list(app.get_releases('web')))
        self.assertEqual([service], list(app.get_releases('service')))
        self.assertEqual([('desktop', [desktop]), ('web', [web]), ('service', [service])],
                         [(platform, list(releases)) for platform, releases in app.releases_by_platform])

    def test_update_has_releases_sees_new_releases_of_any_type(self):
        app = self.loaded()
        self.assertFalse(app.has_web)
        self.add_web()
        app.update_has_releases()
        self.assertTrue(app.has_web)
        self.assertTrue(self.loaded().has_releases)
        WebBundleRelease.objects.filter(app=self.app).update(active=False)
        app.update_has_releases()
        self.assertFalse(app.has_web)
        self.assertFalse(self.loaded().has_releases)

    def test_listing_loads_platforms_in_one_query(self):
        for i in range(10):
            app = App.objects.create(name='app%d' % i, fullname='App %d' % i, active=True)
            ServiceRelease.objects.create(app=app, version='1.0', service_endpoint='https://example.org')
        with self.assertNumQueries(1):
            platforms = [app.platforms for app in App.objects.filter(name__startswith='app')]
        self.assertEqual([[Platform.SERVICE]] * 10, platforms)


class PlatformListingsTestCase(TestCase):
    """Platform pages list every app on the platform; 2.x-only plugins get their own page (#155)."""

    def setUp(self):
        self.multi = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True)
        Release.objects.create(app=self.multi, version='1.0', works_with='3.10')
        WebBundleRelease.objects.create(app=self.multi, version='1.0', active=True, bundle_hash='0')
        ServiceRelease.objects.create(app=self.multi, version='1.0', service_endpoint='https://example.org/multi')
        self.legacy = App.objects.create(name='legacy', fullname='Legacy Plugin', active=True,
                                         cy_2x_plugin_download='https://example.org/legacy.jar')
        App.objects.create(name='empty', fullname='Empty App', active=True)

    def listed(self, url):
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        return {app.fullname for app in response.context['apps']}

    def test_an_app_is_listed_on_each_of_its_platforms(self):
        for platform in ('desktop', 'web', 'service'):
            self.assertEqual({'Multi'}, self.listed('/apps/platform/%s/' % platform))

    def test_unknown_platform_is_404(self):
        self.assertEqual(404, self.client.get('/apps/platform/bogus/').status_code)

    def test_legacy_plugins_are_listed_only_on_their_own_page(self):
        response = self.client.get('/apps/cy2x_plugins')
        self.assertContains(response, 'Legacy Plugin')
        self.assertNotContains(response, 'Empty App')
        self.assertEqual({'Legacy Plugin'}, {app.fullname for app in response.context['apps']})
        self.assertNotContains(self.client.get('/apps/platform/desktop/'), 'Unsupported Plugins')

    def test_nav_panel_links_to_legacy_plugins(self):
        self.assertContains(self.client.get('/apps/all'), 'href="/apps/cy2x_plugins"')


class _ElementIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for name, value in attrs if name == 'id')


class UnifiedAppPageTestCase(TestCase):
    """One app page shows every platform the app is on (#155)."""

    PANELS = {'desktop': 'cy-app-panel-desktop', 'web': 'cy-app-panel-web', 'service': 'cy-app-panel-service'}

    def setUp(self):
        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.other = User.objects.create_user('other', 'other@example.org', 'secret')
        self.apps = {}
        for name, platforms in (('desktoponly', ['desktop']), ('webonly', ['web']),
                                ('serviceonly', ['service']), ('multi', ['desktop', 'web', 'service'])):
            app = App.objects.create(name=name, fullname=name.title(), active=True, has_releases=True)
            app.editors.add(self.editor)
            if 'desktop' in platforms:
                Release.objects.create(app=app, version='1.0', works_with='3.10')
            if 'web' in platforms:
                WebBundleRelease.objects.create(app=app, version='1.0', active=True, bundle_hash='0')
            if 'service' in platforms:
                ServiceRelease.objects.create(app=app, version='1.0', service_endpoint='https://example.org/%s' % name)
            self.apps[name] = platforms

    def page(self, name, query=''):
        response = self.client.get('/apps/%s%s' % (name, query))
        self.assertEqual(200, response.status_code)
        return response.content.decode('utf-8')

    def panel_order(self, content):
        positions = {platform: content.find('id="%s"' % panel) for platform, panel in self.PANELS.items()}
        return sorted((platform for platform, at in positions.items() if at != -1), key=positions.get)

    def chip(self, content, platform):
        return re.search(r'<a href="\?platform=%s" class="btn btn-large[^"]*cy-app-platform-chip"[^>]*>' % platform, content)

    def test_panels_and_a_selector_button_per_platform(self):
        for name, platforms in self.apps.items():
            content = self.page(name)
            self.assertEqual(platforms, self.panel_order(content), name)
            for platform in self.PANELS:
                self.assertEqual(platform in platforms, bool(self.chip(content, platform)), (name, platform))
            # Release History lists the selected (first) platform only, with no second set of buttons
            self.assertEqual([platforms[0]], [p for p in self.PANELS if 'id="cy-app-releases-%s"' % p in content], name)
            self.assertNotIn('cy-app-release-platforms', content, name)

    def test_selector_marks_the_selected_platform(self):
        for query, selected in (('', 'desktop'), ('?platform=web', 'web'), ('?platform=service', 'service'),
                                ('?platform=bogus', 'desktop')):
            content = self.page('multi', query)
            for platform in self.PANELS:
                tag = self.chip(content, platform).group(0)
                self.assertEqual(platform == selected, 'btn-primary active' in tag and 'aria-current="true"' in tag,
                                 (query, platform))

    def test_release_history_lists_the_selected_platform(self):
        for platform, heading in (('desktop', 'Cytoscape Desktop releases'), ('web', 'Cytoscape Web releases'),
                                  ('service', 'Service releases')):
            releases_tab = self.page('multi', '?platform=' + platform).split('id="cy-app-releases-tab"', 1)[1]
            self.assertIn('<h3 class="cy-app-releases-heading">%s</h3>' % heading, releases_tab)
            self.assertEqual([platform], [p for p in self.PANELS if 'id="cy-app-releases-%s"' % p in releases_tab])

    def test_no_duplicate_element_ids(self):
        for name in self.apps:
            parser = _ElementIds()
            parser.feed(self.page(name))
            duplicates = {i for i in parser.ids if parser.ids.count(i) > 1}
            self.assertEqual(set(), duplicates, name)

    def test_selected_platform_comes_first(self):
        self.assertEqual(['web', 'desktop', 'service'], self.panel_order(self.page('multi', '?platform=web')))
        self.assertEqual(['service', 'desktop', 'web'], self.panel_order(self.page('multi', '?platform=service')))

    def test_invalid_platform_falls_back_to_the_first(self):
        self.assertEqual(['desktop', 'web', 'service'], self.panel_order(self.page('multi', '?platform=bogus')))
        self.assertEqual(['web'], self.panel_order(self.page('webonly', '?platform=desktop')))

    def test_install_buttons_set_up_per_platform(self):
        content = self.page('multi')
        self.assertIn("AppPage.setup_install('#cy-app-install-btn-desktop'", content)
        self.assertIn("'selector': '#cy-app-install-btn-service'", content)
        self.assertIn('Install service app in Cytoscape Desktop', content)
        self.assertNotIn('AppPage.setup_install(', self.page('webonly'))

    def test_editor_menu_offers_every_platform_to_editors_only(self):
        submit_links = ('/submit/submit_desktop_app?expect_app_name=Multi',
                        '/submit/submit_web_bundle?expect_app_name=Multi',
                        '/submit/submit_service_app?expect_app_name=Multi')
        self.client.force_login(self.editor)
        content = self.page('multi')
        for link in submit_links:
            self.assertIn(link, content)
        self.client.force_login(self.other)
        content = self.page('multi')
        for link in submit_links:
            self.assertNotIn(link, content)


class PlatformTilesTestCase(TestCase):
    """App tiles show a sticker per platform and say downloads or installs (#155)."""

    def tile(self, platforms):
        name = 'app' + ''.join(platforms)
        app = App.objects.create(name=name, fullname=name, active=True, has_releases=bool(platforms))
        if 'desktop' in platforms:
            Release.objects.create(app=app, version='1.0', works_with='3.10')
        if 'web' in platforms:
            WebBundleRelease.objects.create(app=app, version='1.0', active=True, bundle_hash='0')
        if 'service' in platforms:
            ServiceRelease.objects.create(app=app, version='1.0', service_endpoint='https://example.org/app')
        app = App.objects.get(pk=app.pk)
        return Template('{% load app_buttons %}{% app_button app 0 %}').render(Context({'app': app}))

    def stickers(self, html):
        return re.findall(r'cy-sticker-(desktop|web)', html)

    def usage(self, html):
        found = re.search(r'class="cy-app-usage">\d+ (\w+)<', html)
        return found.group(1) if found else None

    def test_stickers_and_usage_per_platform_set(self):
        for platforms, stickers, usage in ((['desktop'], ['desktop'], 'downloads'),
                                           (['web'], ['web'], 'installs'),
                                           (['service'], ['web'], 'installs'),
                                           (['desktop', 'web', 'service'], ['desktop', 'web'], 'downloads'),
                                           ([], [], None)):
            html = self.tile(platforms)
            self.assertEqual(stickers, self.stickers(html), platforms)
            self.assertEqual(usage, self.usage(html), platforms)
        self.assertIn('cy-sticker-second', self.tile(['desktop', 'service']))


class EditPageReleasesByPlatformTestCase(TestCase):
    """The edit page's release notes and deletes name the platform, since release ids are per platform (#155)."""

    def setUp(self):
        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.app = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True)
        self.app.editors.add(self.editor)
        self.desktop = Release.objects.create(app=self.app, version='1.0', works_with='3.10')
        self.web = WebBundleRelease.objects.create(app=self.app, version='1.0', active=True, bundle_hash='0')
        self.service = ServiceRelease.objects.create(app=self.app, version='1.0', service_endpoint='https://example.org/multi')
        self.client.force_login(self.editor)

    def post(self, action, platform, release, **data):
        data.update({'action': action, 'release_count': 1, 'release_id_0': release.id})
        if platform:
            data['platform'] = platform
        return self.client.post('/apps/multi/edit', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_edit_page_lists_the_selected_platforms_releases(self):
        releases = {'desktop': self.desktop, 'web': self.web, 'service': self.service}
        for selected, heading in (('desktop', 'Cytoscape Desktop releases'), ('web', 'Cytoscape Web releases'),
                                  ('service', 'Service releases')):
            content = self.client.get('/apps/multi/edit?platform=' + selected).content.decode('utf-8')
            self.assertIn('<h3 class="cy-app-releases-heading">%s</h3>' % heading, content)
            self.assertNotIn('cy-release-platform', content)
            for platform, release in releases.items():
                self.assertEqual(platform == selected,
                                 'release_id="%d" data-platform="%s"' % (release.id, platform) in content, (selected, platform))

    def test_notes_go_to_the_named_platforms_release(self):
        self.assertEqual(200, self.post('save_release_notes', 'web', self.web, notes_0='web notes').status_code)
        self.web.refresh_from_db()
        self.desktop.refresh_from_db()
        self.assertEqual('web notes', self.web.notes)
        self.assertFalse(self.desktop.notes)

    def test_platform_is_required_when_the_app_has_several_platforms(self):
        for action, extra in (('save_release_notes', {'notes_0': 'notes'}), ('delete_release', {})):
            response = self.post(action, None, self.web, **extra)
            self.assertContains(response, 'platform is required when an app has releases on more than one platform',
                                status_code=400)
        self.web.refresh_from_db()
        self.assertEqual((True, None), (self.web.active, self.web.notes))

    def test_unknown_platform_is_rejected(self):
        response = self.post('save_release_notes', 'bogus', self.web, notes_0='notes')
        self.assertContains(response, 'platform must be one of', status_code=400)

    def test_deleting_the_last_web_release_takes_the_app_off_web(self):
        self.assertEqual(200, self.post('delete_release', 'web', self.web).status_code)
        self.web.refresh_from_db()
        self.desktop.refresh_from_db()
        self.assertFalse(self.web.active)
        self.assertTrue(self.desktop.active)
        app = App.objects.get(name='multi')
        self.assertEqual([Platform.DESKTOP, Platform.SERVICE], app.platforms)
        self.assertNotContains(self.client.get('/apps/platform/web/'), 'Multi')
        self.assertContains(self.client.get('/apps/platform/desktop/'), 'Multi')


class EditPageDefaultPlatformTestCase(TestCase):
    """
    Release-notes and delete-release edits without a platform field apply to the
    app's one released platform; the edit page sent no platform before #155.
    """

    def setUp(self):
        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.app = App.objects.create(name='webonly', fullname='Web Only', active=True, has_releases=True)
        self.app.editors.add(self.editor)
        self.web = WebBundleRelease.objects.create(app=self.app, version='1.0', active=True, bundle_hash='0')
        self.old_web = WebBundleRelease.objects.create(app=self.app, version='0.9', active=True, bundle_hash='1')
        self.client.force_login(self.editor)

    def post(self, action, release, **data):
        data.update({'action': action, 'release_count': 1, 'release_id_0': release.id})
        return self.client.post('/apps/webonly/edit', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_notes_without_platform_go_to_the_apps_only_platform(self):
        self.assertEqual(200, self.post('save_release_notes', self.web, notes_0='web notes').status_code)
        self.web.refresh_from_db()
        self.assertEqual('web notes', self.web.notes)

    def test_delete_without_platform_applies_to_the_apps_only_platform(self):
        self.assertEqual(200, self.post('delete_release', self.old_web).status_code)
        self.old_web.refresh_from_db()
        self.assertFalse(self.old_web.active)
        self.assertEqual([Platform.WEB], App.objects.get(name='webonly').platforms)

    def test_app_without_releases_must_name_a_platform(self):
        WebBundleRelease.objects.filter(app=self.app).update(active=False)
        response = self.post('save_release_notes', self.web, notes_0='notes')
        self.assertContains(response, 'platform is required', status_code=400)


class AppPlatformFieldRemovedTestCase(TestCase):

    def test_app_has_no_stored_platform(self):
        with self.assertRaises(FieldDoesNotExist):
            App._meta.get_field('platform')


class AppContentTestCase(TestCase):
    """Each platform's page content, falling back to the app's own (#155)."""

    def setUp(self):
        self.app = App.objects.create(name='multi', fullname='Multi', active=True, description='Shared description',
                                      details='Shared details', website='https://example.org/shared',
                                      license_text='https://example.org/license', license_confirm=True)
        self.app.tags.add(Tag.objects.create(name='shared', fullname='shared'))
        self.shot = Screenshot.objects.create(app=self.app, screenshot='multi/shot.png', thumbnail='multi/shot_t.png')
        OrderedAuthor.objects.create(app=self.app, author=Author.objects.create(name='Shared Author'), author_order=0)

    def snapshot(self, content):
        return {'description': content.description, 'details': content.details, 'website': content.website,
                'license': (content.license_text, content.license_confirm),
                'tags': [tag.name for tag in content.tags], 'screenshots': [s.screenshot.name for s in content.screenshots],
                'authors': [author.name for author in content.authors]}

    SHARED = {'description': 'Shared description', 'details': 'Shared details', 'website': 'https://example.org/shared',
              'license': ('https://example.org/license', True), 'tags': ['shared'],
              'screenshots': ['multi/shot.png'], 'authors': ['Shared Author']}

    def test_desktop_reads_the_app(self):
        self.assertEqual(self.SHARED, self.snapshot(self.app.content(Platform.DESKTOP)))
        self.assertEqual(self.SHARED, self.snapshot(self.app.content()))

    def test_platform_without_content_shows_the_apps(self):
        for platform in (Platform.WEB, Platform.SERVICE):
            self.assertEqual(self.SHARED, self.snapshot(self.app.content(platform)), platform)

    def test_platform_with_content_shows_its_own(self):
        own = AppPlatformContent.objects.create(app=self.app, platform=Platform.WEB, description='Web description',
                                                details='Web details')
        own.tags.add(Tag.objects.create(name='webonly', fullname='web only'))
        OrderedAuthor.objects.create(app=self.app, platform=Platform.WEB,
                                     author=Author.objects.create(name='Web Author'), author_order=0)
        self.assertEqual({'description': 'Web description', 'details': 'Web details', 'website': None,
                          'license': (None, False), 'tags': ['webonly'], 'screenshots': [],
                          'authors': ['Web Author']},
                         self.snapshot(self.app.content(Platform.WEB)))
        # the others are untouched by it
        self.assertEqual(self.SHARED, self.snapshot(self.app.content(Platform.DESKTOP)))
        self.assertEqual(self.SHARED, self.snapshot(self.app.content(Platform.SERVICE)))
        self.assertEqual(['Shared Author'], [author.name for author in self.app.ordered_authors])

    def test_first_edit_copies_what_the_platform_showed(self):
        own = self.app.content_for_edit(Platform.WEB)
        self.assertIsInstance(own, AppPlatformContent)
        self.assertEqual(self.SHARED, self.snapshot(self.app.content(Platform.WEB)))
        web_shot = self.app.content(Platform.WEB).screenshots.get()
        self.assertNotEqual(self.shot.id, web_shot.id)
        self.assertEqual(self.shot.thumbnail.name, web_shot.thumbnail.name)

        own.details = 'Web details'
        own.save()
        own.tags.clear()
        self.assertEqual('Web details', self.app.content(Platform.WEB).details)
        self.assertEqual([], list(self.app.content(Platform.WEB).tags))
        self.app.refresh_from_db()
        self.assertEqual(self.SHARED, self.snapshot(self.app.content(Platform.DESKTOP)))
        # a second edit reuses it
        self.assertEqual(own.id, self.app.content_for_edit(Platform.WEB).id)
        self.assertEqual(1, AppPlatformContent.objects.count())

    def test_desktop_edits_go_to_the_app(self):
        self.assertIs(self.app, self.app.content_for_edit(Platform.DESKTOP))
        self.assertIs(self.app, self.app.content_for_edit(None))
        self.assertEqual(0, AppPlatformContent.objects.count())
        with self.assertRaises(ValueError):
            self.app.content_for_edit('bogus')

    def test_deleting_the_app_deletes_its_content(self):
        self.app.content_for_edit(Platform.SERVICE)
        self.app.delete()
        self.assertEqual(0, AppPlatformContent.objects.count())
        self.assertEqual(0, Screenshot.objects.count())
        self.assertEqual(0, OrderedAuthor.objects.count())


class PlatformContentPageTestCase(TestCase):
    """The app page shows the selected platform's content (#155)."""

    def setUp(self):
        self.app = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True,
                                      description='Desktop description', details='Desktop details',
                                      website='https://example.org/desktop', citation='111',
                                      license_text='https://example.org/desktop-license', license_confirm=True,
                                      cy_2x_plugin_download='https://example.org/multi.jar', cy_2x_plugin_version='0.9')
        self.app.tags.add(Tag.objects.create(name='desktoptag', fullname='desktop tag'))
        OrderedAuthor.objects.create(app=self.app, author=Author.objects.create(name='Desktop Author'), author_order=0)
        Release.objects.create(app=self.app, version='1.0', works_with='3.10')
        WebBundleRelease.objects.create(app=self.app, version='1.0', active=True, bundle_hash='0')
        ServiceRelease.objects.create(app=self.app, version='1.0', service_endpoint='https://example.org/multi')
        web = AppPlatformContent.objects.create(app=self.app, platform=Platform.WEB, description='Web description',
                                                details='Web details', website='https://example.org/web',
                                                citation='222', license_text='https://example.org/web-license')
        web.tags.add(Tag.objects.create(name='webtag', fullname='web tag'))
        OrderedAuthor.objects.create(app=self.app, platform=Platform.WEB,
                                     author=Author.objects.create(name='Web Author'), author_order=0)

    def page(self, query=''):
        response = self.client.get('/apps/multi' + query)
        self.assertEqual(200, response.status_code)
        return response.content.decode('utf-8')

    DESKTOP = ('Desktop description', 'Desktop details', 'desktop tag', 'Desktop Author',
               'href="https://example.org/desktop"', 'from_uid=111')
    WEB = ('Web description', 'Web details', 'web tag', 'Web Author', 'href="https://example.org/web"', 'from_uid=222')

    def test_each_platform_shows_its_own_content(self):
        for query, shown, hidden in (('?platform=web', self.WEB, self.DESKTOP), ('?platform=desktop', self.DESKTOP, self.WEB),
                                     ('', self.DESKTOP, self.WEB)):
            content = self.page(query)
            for text in shown:
                self.assertIn(text, content, (query, text))
            for text in hidden:
                self.assertNotIn(text, content, (query, text))

    def test_platform_without_content_shows_the_apps(self):
        content = self.page('?platform=service')
        for text in self.DESKTOP:
            self.assertIn(text, content, text)
        for text in self.WEB:
            self.assertNotIn(text, content, text)

    def test_each_panel_shows_its_own_license(self):
        content = self.page('?platform=web')
        # each panel runs to the next panel's opening tag
        panels = {platform: content.split('id="cy-app-panel-%s"' % platform, 1)[1].split('<div class="well', 1)[0]
                  for platform in ('desktop', 'web', 'service')}
        self.assertIn('https://example.org/desktop-license', panels['desktop'])
        self.assertIn('https://example.org/web-license', panels['web'])
        self.assertNotIn('desktop-license', panels['web'])
        # the service version has no content of its own, so the app's license
        self.assertIn('https://example.org/desktop-license', panels['service'])

    def test_license_dialog_per_platform_that_asks_for_it(self):
        AppPlatformContent.objects.create(app=self.app, platform=Platform.SERVICE, license_confirm=True,
                                          license_text='https://example.org/service-license')
        content = self.page()
        self.assertIn('<div class="modal hide fade in cy-license-modal" id="license_modal_desktop"', content)
        self.assertIn('data-src="https://example.org/desktop-license"', content)
        self.assertIn('id="license_modal_service"', content)
        self.assertIn('data-src="https://example.org/service-license"', content)
        self.assertNotIn('id="license_modal_web"', content)
        self.assertNotIn('id="license_modal"', content)

    def test_cytoscape_2_panel_only_with_desktop(self):
        self.assertIn('id="cy-app-panel-cy2x"', self.page('?platform=desktop'))
        self.assertNotIn('id="cy-app-panel-cy2x"', self.page('?platform=web'))
        self.assertNotIn('id="cy-app-panel-cy2x"', self.page('?platform=service'))

    def test_shared_name_and_counts_on_every_platform(self):
        for query in ('?platform=desktop', '?platform=web', '?platform=service'):
            content = self.page(query)
            self.assertIn('<h2 id="app-name">\n\t\t\tMulti\n\t\t</h2>', content, query)
            self.assertIn('0 downloads', content, query)


class EditPagePlatformContentTestCase(TestCase):
    """The edit page edits the selected platform's content (#155)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.media = self.settings(MEDIA_ROOT=self.tmp)
        self.media.enable()
        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.app = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True,
                                      description='Desktop description', details='Desktop details',
                                      website='https://example.org/desktop')
        self.app.editors.add(self.editor)
        self.app.tags.add(Tag.objects.create(name='desktoptag', fullname='desktop tag'))
        OrderedAuthor.objects.create(app=self.app, author=Author.objects.create(name='Desktop Author'), author_order=0)
        self.shot = Screenshot.objects.create(app=self.app, screenshot='multi/shot.png', thumbnail='multi/shot_t.png')
        Release.objects.create(app=self.app, version='1.0', works_with='3.10')
        WebBundleRelease.objects.create(app=self.app, version='1.0', active=True, bundle_hash='0')
        self.client.force_login(self.editor)

    def tearDown(self):
        self.media.disable()
        shutil.rmtree(self.tmp)

    def post(self, data, platform='web'):
        if platform:
            data = dict(data, platform=platform)
        return self.client.post('/apps/multi/edit', data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def assert_desktop_unchanged(self):
        app = App.objects.get(name='multi')
        desktop = app.content(Platform.DESKTOP)
        self.assertEqual(('Desktop description', 'Desktop details', 'https://example.org/desktop'),
                         (desktop.description, desktop.details, desktop.website))
        self.assertEqual(['desktop tag'], [t.fullname for t in desktop.tags])
        self.assertEqual(['Desktop Author'], [a.name for a in desktop.authors])
        self.assertEqual([self.shot.id], [s.id for s in desktop.screenshots])

    def test_each_field_with_web_changes_only_the_web_content(self):
        for action, field, value in (('save_description', 'description', 'Web description'),
                                     ('save_details', 'details', 'Web details'),
                                     ('save_website', 'website', 'https://example.org/web'),
                                     ('save_tutorial', 'tutorial', 'https://example.org/web-tutorial'),
                                     ('save_citation', 'citation', '222'),
                                     ('save_coderepo', 'coderepo', 'https://example.org/web-code'),
                                     ('save_automation', 'automation', 'https://example.org/web-automation'),
                                     ('save_contact', 'contact', 'web@example.org'),
                                     ('save_license_text', 'license_text', 'https://example.org/web-license')):
            self.assertEqual(200, self.post({'action': action, field: value}).status_code, action)
            self.assertEqual(value, getattr(App.objects.get(name='multi').content(Platform.WEB), field), action)
        self.assertEqual(200, self.post({'action': 'save_license_confirm', 'license_confirm': 'true'}).status_code)
        self.assertTrue(App.objects.get(name='multi').content(Platform.WEB).license_confirm)
        self.assert_desktop_unchanged()
        content = self.client.get('/apps/multi?platform=web').content.decode('utf-8')
        self.assertIn('Web details', content)
        self.assertNotIn('Desktop details', content)
        self.assertIn('Desktop details', self.client.get('/apps/multi?platform=desktop').content.decode('utf-8'))

    def test_tags_and_authors_with_web_change_only_the_web_content(self):
        self.assertEqual(200, self.post({'action': 'save_tags', 'tag_count': 1, 'tag_0': 'web tag'}).status_code)
        self.assertEqual(200, self.post({'action': 'save_authors', 'authors_count': 1, 'author_0': 'Web Author',
                                         'institution_0': 'Web Institute'}).status_code)
        web = App.objects.get(name='multi').content(Platform.WEB)
        self.assertEqual(['web tag'], [t.fullname for t in web.tags])
        self.assertEqual([('Web Author', 'Web Institute')], [(a.name, a.institution) for a in web.authors])
        self.assert_desktop_unchanged()
        # and saving the desktop authors leaves the web ones
        self.assertEqual(200, self.post({'action': 'save_authors', 'authors_count': 1, 'author_0': 'New Desktop Author'},
                                        platform='desktop').status_code)
        self.assertEqual(['Web Author'], [a.name for a in App.objects.get(name='multi').content(Platform.WEB).authors])
        self.assertEqual(['New Desktop Author'], [a.name for a in App.objects.get(name='multi').ordered_authors])

    def test_screenshots_with_web_change_only_the_web_content(self):
        image = io.BytesIO()
        Image.new('RGB', (20, 20)).save(image, 'PNG')
        upload = SimpleUploadedFile('web.png', image.getvalue(), content_type='image/png')
        self.assertEqual(200, self.post({'action': 'upload_screenshot', 'file': upload}).status_code)
        web = App.objects.get(name='multi').content(Platform.WEB)
        # the first edit copied the app's screenshot, then added the new one
        self.assertEqual(2, web.screenshots.count())
        self.assert_desktop_unchanged()
        content = self.client.get('/apps/multi?platform=web').content.decode('utf-8')
        new_shot = web.screenshots.last()
        self.assertIn(new_shot.thumbnail.url, content)
        self.assertNotIn(new_shot.thumbnail.url, self.client.get('/apps/multi?platform=desktop').content.decode('utf-8'))

    def test_deleting_a_screenshot_the_web_page_showed_before_its_first_edit(self):
        # the web edit page showed the app's screenshot (its id), as web had no content yet
        self.assertEqual(200, self.post({'action': 'delete_screenshot', 'screenshot_id': self.shot.id}).status_code)
        self.assertEqual(0, App.objects.get(name='multi').content(Platform.WEB).screenshots.count())
        self.assert_desktop_unchanged()

    def test_screenshot_of_another_app_or_platform_cannot_be_deleted(self):
        other = App.objects.create(name='other', fullname='Other', active=True)
        other_shot = Screenshot.objects.create(app=other, screenshot='other/shot.png', thumbnail='other/shot_t.png')
        response = self.post({'action': 'delete_screenshot', 'screenshot_id': other_shot.id}, platform='desktop')
        self.assertContains(response, 'invalid screenshot_id', status_code=400)
        self.assertTrue(Screenshot.objects.filter(id=other_shot.id).exists())
        web_shot = Screenshot.objects.create(app=self.app, platform=Platform.WEB, screenshot='multi/web.png',
                                             thumbnail='multi/web_t.png')
        response = self.post({'action': 'delete_screenshot', 'screenshot_id': web_shot.id}, platform='desktop')
        self.assertContains(response, 'invalid screenshot_id', status_code=400)
        self.assertTrue(Screenshot.objects.filter(id=web_shot.id).exists())

    def test_without_a_platform_edits_the_app_as_before(self):
        self.assertEqual(200, self.post({'action': 'save_details', 'details': 'Changed details'}, platform=None).status_code)
        self.assertEqual('Changed details', App.objects.get(name='multi').details)
        self.assertEqual(0, AppPlatformContent.objects.count())

    def test_platform_must_be_one_the_app_is_on(self):
        for platform in ('bogus', 'service'):
            response = self.post({'action': 'save_details', 'details': 'x'}, platform=platform)
            self.assertContains(response, 'platform must be one this app is on', status_code=400)
        self.assertEqual(0, AppPlatformContent.objects.count())

    def test_edit_page_shows_the_selected_platforms_content(self):
        self.post({'action': 'save_details', 'details': 'Web details'})
        web_page = self.client.get('/apps/multi/edit?platform=web').content.decode('utf-8')
        self.assertIn('>Web details</textarea>', web_page)
        self.assertIn("AppPageEdit.set_platform('web');", web_page)
        self.assertIn('AppPageEdit.set_app_page_url("/apps/multi?platform=web");', web_page)
        self.assertNotIn('Cytoscape 2.x Plugin', web_page)
        desktop_page = self.client.get('/apps/multi/edit?platform=desktop').content.decode('utf-8')
        self.assertIn('>Desktop details</textarea>', desktop_page)
        self.assertIn('Cytoscape 2.x Plugin', desktop_page)
        # an unknown platform edits the primary one
        self.assertIn("AppPageEdit.set_platform('desktop');",
                      self.client.get('/apps/multi/edit?platform=bogus').content.decode('utf-8'))

    def test_editor_menu_edits_the_selected_platform(self):
        content = self.client.get('/apps/multi?platform=web').content.decode('utf-8')
        self.assertIn('<a href="/apps/multi/edit?platform=web">Edit this page</a>', content)


class PlatformContentListingsTestCase(TestCase):
    """Listings, category pages, search and the Desktop feed with per-platform content (#155)."""

    def setUp(self):
        apps_views._flush_tag_caches()
        self.app = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True,
                                      description='Desktop description', details='Desktop details')
        self.desktop_tag = Tag.objects.create(name='desktoptag', fullname='desktop tag')
        self.app.tags.add(self.desktop_tag)
        Release.objects.create(app=self.app, version='1.0', works_with='3.10')
        WebBundleRelease.objects.create(app=self.app, version='1.0', active=True, bundle_hash='0')
        web = AppPlatformContent.objects.create(app=self.app, platform=Platform.WEB, description='Web description',
                                                details='Web details mentioning browsers')
        self.web_tag = Tag.objects.create(name='webtag', fullname='web tag')
        web.tags.add(self.web_tag)

    def tearDown(self):
        apps_views._flush_tag_caches()

    def test_platform_listing_tiles_describe_that_platform(self):
        web = self.client.get('/apps/platform/web/').content.decode('utf-8')
        self.assertIn('Web description', web)
        self.assertNotIn('Desktop description', web)
        desktop = self.client.get('/apps/platform/desktop/').content.decode('utf-8')
        self.assertIn('Desktop description', desktop)
        self.assertNotIn('Web description', desktop)
        # other lists use the primary platform's
        self.assertIn('Desktop description', self.client.get('/apps/all').content.decode('utf-8'))

    def test_web_only_app_tile_uses_its_web_content(self):
        app = App.objects.create(name='webonly', fullname='Web Only', active=True, has_releases=True,
                                 description='App description')
        WebBundleRelease.objects.create(app=app, version='1.0', active=True, bundle_hash='0')
        AppPlatformContent.objects.create(app=app, platform=Platform.WEB, description='Its web description')
        self.assertIn('Its web description', self.client.get('/apps/all').content.decode('utf-8'))

    def test_category_pages_list_apps_with_it_on_any_platform(self):
        for tag in ('webtag', 'desktoptag'):
            self.assertIn('<h5>Multi</h5>', self.client.get('/apps/with_tag/%s' % tag).content.decode('utf-8'), tag)
        self.assertEqual(1, self.web_tag.count)
        self.assertEqual(1, self.desktop_tag.count)
        # an app with the category on the app and a platform counts once
        AppPlatformContent.objects.get(app=self.app).tags.add(self.desktop_tag)
        apps_views._flush_tag_caches()
        self.assertEqual(1, Tag.objects.get(name='desktoptag').count)

    def test_search_indexes_every_platforms_content(self):
        from haystack import connections
        text = connections['default'].get_unified_index().get_index(App).prepare(self.app)['text']
        self.assertIn('Desktop details', text)
        self.assertIn('Web details mentioning browsers', text)
        self.assertIn('Web description', text)

    def test_desktop_feed_keeps_the_apps_own_content(self):
        [entry] = [a for a in json.loads(self.client.get('/backend/all_apps').content) if a['fullname'] == 'Multi']
        self.assertEqual('Desktop description', entry['description'])
        self.assertEqual(['desktop tag'], entry['tags'])


class AuthorPageTestCase(TestCase):
    """An app lists each author once, whichever platforms' content names them (#155)."""

    def test_app_listed_once_after_a_platform_copies_its_authors(self):
        app = App.objects.create(name='multi', fullname='Multi', active=True, has_releases=True)
        Release.objects.create(app=app, version='1.0', works_with='3.10')
        WebBundleRelease.objects.create(app=app, version='1.0', active=True, bundle_hash='0')
        OrderedAuthor.objects.create(app=app, author=Author.objects.create(name='Shared Author'), author_order=0)
        app.content_for_edit(Platform.WEB)  # copies the author for the web content
        self.assertEqual(2, OrderedAuthor.objects.filter(app=app).count())

        content = self.client.get('/apps/with_author/Shared Author').content.decode('utf-8')
        # each tile shows the name twice (compact and full)
        self.assertEqual(2, content.count('<h5>Multi</h5>'))
        self.assertEqual(['Shared Author'], [a.name for a in app.authors.distinct()])

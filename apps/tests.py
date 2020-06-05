"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import io
import os
import shutil
import zipfile
import tempfile
import random
from PIL import Image, ImageDraw

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from apps.models import App
from apps.models import Author
from apps.models import OrderedAuthor
from apps.models import Screenshot
from apps.models import ReleaseAPI
from apps.models import Tag
from apps import models as apps_models
from apps.models import Release
from apps.views import _AppPageEditConfig

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
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from apps.models import App
from apps.models import Author
from apps.models import Tag
from apps import models as apps_models

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)

class AuthorTestCase(TestCase):

    def setUp(self):
        Author.objects.create(name='Bob Smith',
                              institution='U of U')
        Author.objects.create(name='Joe Joe')

        # make an empty author
        Author.objects.create()

    def test_str_for_author_objects(self):
        bob = Author.objects.get(name='Bob Smith')
        self.assertEqual('Bob Smith (U of U)', str(bob))

        joe = Author.objects.get(name='Joe Joe')
        self.assertEqual('Joe Joe', str(joe))

        empty = Author.objects.get(name='')
        self.assertEqual('', str(empty))


class TagTestCase(TestCase):

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
        blah_app_obj.editors = [euser]
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





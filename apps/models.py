import re
import hashlib
import shutil
import subprocess
from os import mkdir, devnull
import logging
import os.path
from os.path import join as pathjoin
from urllib.parse import urljoin
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse


LOGGER = logging.getLogger(__name__)


class Author(models.Model):
    name = models.CharField(max_length=255)
    institution = models.CharField(max_length=255, null=True, blank=True)

    search_schema = ('name', 'institution')
    search_key = 'id'

    def __str__(self):
        if not self.institution:
            return self.name
        else:
            return self.name + ' (' + self.institution + ')'

"""
:py:func:`dict` where key is :py:class:`~Tag` name
and value is count of :py:class:`~App` objects
with that tag name
Populated by a call to :py:func:`~Tag.count`
"""
_TagCountCache = dict()


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    fullname = models.CharField(max_length=255)

    @property
    def count(self):
        global _TagCountCache
        if self.name in _TagCountCache:
            count = _TagCountCache[self.name]
        else:
            count = App.objects.filter(active=True, tags=self).count()
            _TagCountCache[self.name] = count
        return count

    search_schema = ('fullname', )
    search_key = 'name'

    def __str__(self):
        return self.name

    class Meta:
        """
        Dictates tags are ordered by name
        """
        ordering = ["name"]


GENERIC_ICON_URL = urljoin(settings.STATIC_URL,
                           'apps/img/app_icon_generic.png')


def app_icon_path(app, filename):
    """
    Callable function used by :py:class:`~App` constructor
    to set value of 'icon' to a path to `filename`

    :param app:
    :param filename:
    :return: <app.name>/<filename>
    :rtype str
    """
    return pathjoin(app.name, filename)


class App(models.Model):
    name = models.CharField(max_length=127, unique=True)
    fullname = models.CharField(max_length=127, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    icon = models.ImageField(upload_to=app_icon_path, blank=True,
                             null=True)

    authors = models.ManyToManyField(Author, blank=True,
                                     through='OrderedAuthor')
    editors = models.ManyToManyField(User, blank=True)

    cy_2x_plugin_download = models.URLField(blank=True, null=True)
    cy_2x_plugin_version = models.CharField(max_length=31, blank=True,
                                            null=True)
    cy_2x_plugin_release_date = models.DateField(blank=True, null=True)
    cy_2x_versions = models.CharField(max_length=31, blank=True, null=True)

    latest_release_date = models.DateField(blank=True, null=True)
    has_releases = models.BooleanField(default=False)

    license_text = models.URLField(blank=True, null=True)
    license_confirm = models.BooleanField(default=False)

    website = models.URLField(blank=True, null=True)
    tutorial = models.URLField(blank=True, null=True)
    citation = models.CharField(max_length=31, blank=True, null=True)
    coderepo = models.URLField(blank=True, null=True)
    automation = models.URLField(blank=True, null=True)
    contact = models.EmailField(blank=True, null=True)

    stars = models.PositiveIntegerField(default=0)
    votes = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)

    featured = models.BooleanField(default=False)
    competition_winner_dec_2012 = models.BooleanField(default=False)

    active = models.BooleanField(default=False)

    def is_editor(self, user):
        """
        Denotes if 'user' passed in can edit this App

        :param user: The 'user' to check
        :type user: :py:class:`~django.contrib.auth.models.User`
        :return: `True` if 'user' can edit, `False` otherwise
        :rtype: bool
        """
        if not user:
            return False
        if user.is_staff or user.is_superuser:
            return True
        if user in self.editors.all():
            return True
        li = [usr.email for usr in self.editors.all()]
        return user.email in li

    @staticmethod
    def _camel_case_split(the_str):
        """
        Splits camel cased string

        :param the_str:
        :return:
        :rtype list
        """
        words = [[the_str[0]]]

        for c in the_str[1:]:
            if words[-1][-1].islower() and c.isupper():
                words.append(list(c))
            else:
                words[-1].append(c)

        return [''.join(word) for word in words]

    def camelcase(self):
        """
        Splits 'fullname' by capital characters and returns as
        string with spaces between each word as defined by
        capital letters

        :return:
        :rtype: str
        """
        return ' '.join([c for c in self._camel_case_split(self.fullname)])

    @property
    def stars_percentage(self):
        return 100 * self.stars / self.votes / 5 if self.votes != 0 else 0

    @property
    def icon_url(self):
        return self.icon.url if self.icon else GENERIC_ICON_URL

    @property
    def releases(self):
        return self.release_set.filter(active=True).all()

    def update_has_releases(self):
        self.has_releases = (self.release_set.filter(active=True).count() > 0)
        self.save()

    @property
    def page_url(self):
        return reverse('app_page', args=[self.name])

    @property
    def ordered_authors(self):
        return (a.author for a in OrderedAuthor.objects.filter(app=self))

    search_schema = ('^fullname', 'description', 'details')
    search_key = 'name'

    def __str__(self):
        return self.name


class OrderedAuthor(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    author_order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return str(self.author_order) + ': ' + self.app.name +\
               ' by ' + self.author.name

    class Meta:
        ordering = ["author_order"]


VersionRE = re.compile(r'^(\d+)(?:\.(\d)+)?(?:\.(\d)+)?(?:\.([\w-]+))?$')
"""
Regular expression to verify a valid version
used by :py:func:`~Release.version_tuple` function
"""


def release_file_path(release, filename):
    """
    Callable function used by :py:class:`~Release` constructor
    to set release_file

    :param release:
    :param filename:
    :return: <release.app.name>/releases/<release.version>/<filename>
    :rtype: str
    """
    return pathjoin(release.app.name, 'releases',
                    release.version, filename)


class Release(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    version = models.CharField(max_length=31)
    works_with = models.CharField(max_length=31)
    notes = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    release_file = models.FileField(upload_to=release_file_path)
    hexchecksum = models.CharField(max_length=511, blank=True, null=True)
    dependencies = models.ManyToManyField('self', related_name='dependents',
                                          symmetrical=False)

    @property
    def version_tuple(self):
        matched = VersionRE.match(self.version)
        if not matched:
            return None
        (major, minor, patch, tag) = matched.groups()
        major = int(major)
        minor = int(minor) if minor else None
        patch = int(patch) if patch else None
        return major, minor, patch, tag

    @property
    def created_iso(self):
        return self.created.isoformat()

    @property
    def release_file_url(self):
        return self.release_file.url if self.release_file else None

    @property
    def release_download_url(self):
        return reverse('release_download', args=[self.app.name, self.version])

    def __str__(self):
        return self.app.fullname + ' ' + self.version

    def calc_checksum(self):
        cs = hashlib.sha512()
        f = self.release_file.file
        f.open('rb')
        try:
            while True:
                buf = f.read(128)
                if not buf:
                    break
                cs.update(buf)
            self.hexchecksum = '%s:%s' % (cs.name, cs.hexdigest())
            self.save()
        finally:
            f.close()

    def delete_files(self):
        self.release_file.delete()
        if self.releaseapi_set.count() > 0:
            api = self.releaseapi_set.get()
            api.delete_files()
            api.delete()

    class Meta:
        ordering = ['-created']


def screenshot_path(screenshot, filename):
    """
    Callable function used by :py:class:`~Screenshot`

    :param screenshot:
    :param filename:
    :return:
    """
    return pathjoin(screenshot.app.name, 'screenshots', filename)


def thumbnail_path(screenshot, filename):
    """
    Callable function used by :py:class:`~Screenshot`

    :param screenshot:
    :param filename:
    :return:
    """
    return pathjoin(screenshot.app.name, 'thumbnails', filename)


class Screenshot(models.Model):
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    screenshot = models.ImageField(upload_to=screenshot_path)
    thumbnail = models.ImageField(upload_to=thumbnail_path)

    def __str__(self):
        return '%s - %d' % (self.app.fullname, self.id)


def javadocs_path(release_api, filename):
    """
    Callable function used by :py:class:`~ReleaseApi`

    :param release_api:
    :param filename:
    :return:
    """
    return pathjoin(release_api.release.app.name, 'releases', release_api.release.version, filename)


def pom_xml_path(release_api, filename):
    """
    Callable function used by :py:class:`~ReleaseApi`

    :param release_api:
    :param filename:
    :return:
    """
    return pathjoin(release_api.release.app.name, 'releases', release_api.release.version, filename)


class ReleaseAPI(models.Model):
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    javadocs_jar_file = models.FileField(upload_to=javadocs_path)
    pom_xml_file = models.FileField(upload_to=pom_xml_path)

    def __str__(self):
        return str(self.release)

    def extract_javadocs_jar(self):
        file = self.javadocs_jar_file
        dirpath = file.path + '-extracted'
        if not os.path.exists(dirpath):
            mkdir(dirpath)

        unzip_err = os.path.join(file.path + '.unzip.err')

        ecode = 0
        try:
            with open(devnull, 'w') as devnull_stream:
                with open(unzip_err, 'w') as unzip_err_stream:
                    ecode = subprocess.call(['unzip', file.path, '-d', dirpath],
                                            stdout=devnull_stream,
                                            stderr=unzip_err_stream)
            if ecode != 0:
                e_msg = ''
                if os.path.isfile(unzip_err):
                    with open(unzip_err, 'r') as f:
                        e_msg = f.read(250)

                LOGGER.error('Received non zero exit code ' +
                             str(ecode) + ' attempting to ' +
                             'unzip file  : ' + str(file.path) +
                             ' : ' + str(e_msg))
        finally:
            if os.path.exists(unzip_err):
                os.remove(unzip_err)

    def delete_files(self):
        dirpath = self.javadocs_jar_file.path + '-extracted'
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)
        self.javadocs_jar_file.delete()
        self.pom_xml_file.delete()

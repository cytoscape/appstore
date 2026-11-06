import re
import hashlib
import shutil
import subprocess
from os import mkdir, devnull
import logging
import os.path 
from os.path import join as pathjoin
from urllib.parse import urljoin
from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from urllib.parse import quote
from django.core.exceptions import ImproperlyConfigured


LOGGER = logging.getLogger(__name__)


class Author(models.Model):
    id = models.BigAutoField(primary_key=True)
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
            # apps with the category on any platform: the app's own, or a platform's content (#155)
            count = App.objects.filter(models.Q(tags=self) | models.Q(platform_contents__tags=self),
                                       active=True).distinct().count()
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

ServiceVersionRE = re.compile(r'^\d+(?:\.\d+)*$')

def _service_version_key(version):
    """
    Numeric sort key for a service release version such as 1.10 or 2.0.1,
    with trailing zeros dropped so 1.0 and 1.0.0 compare equal.
    Returns None for versions that aren't dot-separated numbers.
    """
    if not version or not ServiceVersionRE.match(version):
        return None
    parts = [int(part) for part in version.split('.')]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)

class Platform(models.TextChoices):
        DESKTOP = 'desktop', 'Desktop'
        WEB = 'web', 'Web'
        SERVICE = 'service', 'Service'

# App reverse accessor holding each platform's releases, in display order
_PLATFORM_RELEASE_SETS = {
    Platform.DESKTOP: 'release_set',
    Platform.WEB: 'webbundlerelease_set',
    Platform.SERVICE: 'servicerelease_set',
}

def _platform_annotation(platform):
    return 'platform_' + platform


class AppQuerySet(models.QuerySet):
    def on_platform(self, platform):
        """Apps with active releases on 'platform'."""
        return self.filter(**{_platform_annotation(platform): True})

    def legacy_plugins(self):
        """Apps that are only a Cytoscape 2.x plugin: no active release on any platform."""
        return self.filter(**{_platform_annotation(platform): False for platform in _PLATFORM_RELEASE_SETS}) \
                   .exclude(cy_2x_plugin_download__isnull=True).exclude(cy_2x_plugin_download='')


class AppManager(models.Manager.from_queryset(AppQuerySet)):
    """
    Annotates every App with whether it has active releases on each platform,
    so listings learn every app's platforms in the same query that loads them.
    """
    def get_queryset(self):
        release_models = {
            Platform.DESKTOP: Release,
            Platform.WEB: WebBundleRelease,
            Platform.SERVICE: ServiceRelease,
        }
        return super().get_queryset().annotate(**{
            _platform_annotation(platform): models.Exists(
                release_model.objects.filter(app=models.OuterRef('pk'), active=True))
            for platform, release_model in release_models.items()
        })


class App(models.Model):
    id = models.BigAutoField(primary_key=True)
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

    objects = AppManager()

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

    @property
    def servicereleases(self):
        return self.servicerelease_set.filter(active=True).all()

    @property
    def webbundlereleases(self):
        return self.webbundlerelease_set.filter(active=True).all()
    
    @property
    def servicereleases_by_version(self):
        """Active service releases, latest version first; ties and unparseable versions fall back to newest created."""
        def sort_key(release):
            version_key = _service_version_key(release.version)
            return (version_key is not None, version_key or (), release.created)
        return sorted(self.servicereleases, key=sort_key, reverse=True)

    def _has_platform_releases(self, platform):
        annotated = getattr(self, _platform_annotation(platform), None)
        if annotated is not None:
            return annotated
        # loaded without AppManager's annotations, e.g. through release.app
        return getattr(self, _PLATFORM_RELEASE_SETS[platform]).filter(active=True).exists()

    @property
    def has_desktop(self):
        return self._has_platform_releases(Platform.DESKTOP)

    @property
    def has_web(self):
        return self._has_platform_releases(Platform.WEB)

    @property
    def has_service(self):
        return self._has_platform_releases(Platform.SERVICE)

    def has_platform(self, platform):
        return self._has_platform_releases(platform)

    @property
    def platforms(self):
        """Platforms this app has active releases on: desktop, then web, then service."""
        return [platform for platform in _PLATFORM_RELEASE_SETS if self._has_platform_releases(platform)]

    @property
    def primary_platform(self):
        platforms = self.platforms
        return platforms[0] if platforms else None

    def get_releases(self, platform):
        if platform == Platform.SERVICE:
            return self.servicereleases
        elif platform == Platform.WEB:
            return self.webbundlereleases
        return self.releases

    def releases_for_display(self, platform):
        if platform == Platform.SERVICE:
            return self.servicereleases_by_version
        return self.get_releases(platform)

    @property
    def releases_by_platform(self):
        return [(platform, self.releases_for_display(platform)) for platform in self.platforms]

    def _forget_platforms(self):
        for platform in _PLATFORM_RELEASE_SETS:
            self.__dict__.pop(_platform_annotation(platform), None)

    def update_has_releases(self):
        # releases were just added or removed, so annotations loaded with this app are stale
        self._forget_platforms()
        self.has_releases = bool(self.platforms)
        self.save()

    @property
    def page_url(self):
        return reverse('app_page', args=[self.name])

    @property
    def ordered_authors(self):
        # the app's own authors; a platform with content of its own has its own in content(platform).authors
        return (a.author for a in OrderedAuthor.objects.filter(app=self, platform__isnull=True))

    @property
    def content_owner(self):
        """
        The platform whose content is the app's own fields (#155): Desktop when the app is on
        Desktop, since Cytoscape Desktop reads them, else the app's one platform without content
        of its own. Before #155 every app was on one platform, whose content these fields are;
        a platform that joins later gets content of its own (separate_platform_content).
        None when that can't tell, e.g. two non-Desktop platforms without content of their own.
        """
        platforms = self.platforms
        if Platform.DESKTOP in platforms:
            return Platform.DESKTOP
        own = {content.platform for content in self.platform_contents.all()}
        without = [platform for platform in platforms if platform not in own]
        return without[0] if len(without) == 1 else None

    def content(self, platform=None):
        """
        What the app page shows for 'platform' (#155): that platform's own content if it has
        some, the app's own fields for the platform they belong to (content_owner), and
        otherwise nothing. No platform ever shows another platform's content.
        Without a platform, the app's own fields.
        """
        if platform is None:
            return AppContent(self, self, None)
        # all(), so listings that prefetch platform_contents read it without a query per app
        own = next((own for own in self.platform_contents.all() if own.platform == platform), None)
        if own is not None:
            return AppContent(self, own, platform)
        if platform == self.content_owner:
            return AppContent(self, self, None)
        return AppContent(self, None, platform)

    @property
    def tile_description(self):
        """
        The description on the app's tile: its 'listing_platform''s, which a listing of one
        platform's apps sets, else its primary platform's.
        """
        return self.content(getattr(self, 'listing_platform', None) or self.primary_platform).description

    @transaction.atomic
    def content_for_edit(self, platform=None):
        """
        Where an edit to 'platform''s content is saved: the app's own fields for the platform
        they belong to (content_owner), or without a platform; else the platform's own
        content, which its first edit creates empty. Nothing is copied from another platform.
        """
        if platform is None:
            return self
        if platform not in Platform.values:
            raise ValueError('platform must be one of: %s' % ', '.join(Platform.values))
        own = self.platform_contents.filter(platform=platform).first()
        if own is not None:
            return own
        if platform == self.content_owner:
            return self
        if platform == Platform.DESKTOP:
            raise ValueError('%s is not on %s' % (self.name, platform))
        return AppPlatformContent.objects.create(app=self, platform=platform)

    @transaction.atomic
    def separate_platform_content(self, original, apply=True):
        """
        Makes the app's own fields the content of 'original', a platform the app is on, and
        gives each of its other platforms content of its own, empty unless it has some (#155).
        Accepting a new platform runs it with the platform the app was on until then.

        Desktop's content must stay the app's own fields, which Cytoscape Desktop reads, so when
        the app is also on Desktop an 'original' other than Desktop gets those fields moved to
        content of its own, and Desktop's starts empty.

        :return: what it changed, or without 'apply' what it would change, one line each
        """
        platforms = self.platforms
        if original not in platforms:
            raise ValueError('%s is not on %s; it is on: %s'
                             % (self.name, original, ', '.join(platforms) or 'no platform'))
        own = {content.platform for content in self.platform_contents.all()}
        changes = []
        if original != Platform.DESKTOP and Platform.DESKTOP in platforms:
            if original in own:
                changes.append("left as is: %s already has content of its own, so the app's own content "
                               "stays with desktop" % original)
            else:
                changes.append("moved the app's own content to %s; desktop's starts empty" % original)
                if apply:
                    self._move_own_content_to(original)
                own.add(original)
        for platform in platforms:
            if platform in own or platform in (original, Platform.DESKTOP):
                continue
            changes.append('gave %s empty content of its own' % platform)
            if apply:
                AppPlatformContent.objects.create(app=self, platform=platform)
        return changes

    def _move_own_content_to(self, platform):
        """Moves the app's own fields, categories, screenshots and authors to 'platform''s own content."""
        own = AppPlatformContent.objects.create(
            app=self, platform=platform, **{field: getattr(self, field) for field in CONTENT_FIELDS})
        own.tags.set(self.tags.all())
        Screenshot.objects.filter(app=self, platform__isnull=True).update(platform=platform)
        OrderedAuthor.objects.filter(app=self, platform__isnull=True).update(platform=platform)
        for field in CONTENT_FIELDS:
            setattr(self, field, False if field == 'license_confirm' else None)
        self.tags.clear()
        self.save()

    search_schema = ('^fullname', 'description', 'details')
    search_key = 'name'

    def __str__(self):
        return self.name


class OrderedAuthor(models.Model):
    id = models.BigAutoField(primary_key=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    author_order = models.PositiveSmallIntegerField(default=0)
    # the platform whose content lists this author; null for the app's own (Desktop's) authors
    platform = models.CharField(max_length=31, choices=Platform.choices, blank=True, null=True)

    def __str__(self):
        return str(self.author_order) + ': ' + self.app.name +\
               ' by ' + self.author.name

    class Meta:
        ordering = ["author_order"]


# The content fields an app keeps per platform, besides its categories, screenshots and authors
CONTENT_FIELDS = ('description', 'details', 'license_text', 'license_confirm',
                  'website', 'tutorial', 'citation', 'coderepo', 'automation', 'contact')

class AppPlatformContent(models.Model):
    """
    A platform's own page content (#155), for each platform but the one whose content is
    the app's own fields (App.content_owner). The app's name and icon stay shared.
    """
    id = models.BigAutoField(primary_key=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name='platform_contents')
    platform = models.CharField(max_length=31, choices=Platform.choices)

    description = models.CharField(max_length=255, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='platform_contents')

    license_text = models.URLField(blank=True, null=True)
    license_confirm = models.BooleanField(default=False)

    website = models.URLField(blank=True, null=True)
    tutorial = models.URLField(blank=True, null=True)
    citation = models.CharField(max_length=31, blank=True, null=True)
    coderepo = models.URLField(blank=True, null=True)
    automation = models.URLField(blank=True, null=True)
    contact = models.EmailField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['app', 'platform'], name='unique_app_platform_content'),
        ]

    def __str__(self):
        return '%s (%s)' % (self.app.name, self.platform)


class AppContent:
    """
    One platform's page content: the fields of 'source' (the App, or its
    AppPlatformContent), with the screenshots and authors of 'own_platform'
    (None for the app's own). With no 'source', the platform has no content
    yet, and everything is empty.
    """
    def __init__(self, app, source, own_platform):
        self.app = app
        self.own_platform = own_platform
        for field in CONTENT_FIELDS:
            setattr(self, field, getattr(source, field) if source is not None
                                 else (False if field == 'license_confirm' else None))
        self._source = source

    @property
    def tags(self):
        return self._source.tags.all() if self._source is not None else Tag.objects.none()

    @property
    def screenshots(self):
        if self._source is None:
            return Screenshot.objects.none()
        return Screenshot.objects.filter(app=self.app, platform=self.own_platform).order_by('id')

    @property
    def authors(self):
        if self._source is None:
            return []
        return [ordered.author for ordered in OrderedAuthor.objects.filter(app=self.app, platform=self.own_platform)]


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
    id = models.BigAutoField(primary_key=True)
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
    id = models.BigAutoField(primary_key=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    screenshot = models.ImageField(upload_to=screenshot_path)
    thumbnail = models.ImageField(upload_to=thumbnail_path)
    # the platform whose content shows this screenshot; null for the app's own (Desktop's)
    platform = models.CharField(max_length=31, choices=Platform.choices, blank=True, null=True)

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
    id = models.BigAutoField(primary_key=True)
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

class ServiceRelease(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    version = models.CharField(max_length=31)
    service_endpoint = models.URLField(blank=False, null=True)
    description = models.TextField(blank=True)
    citation = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    metadata = models.JSONField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    @property
    def created_iso(self):
        return self.created.isoformat()
    
    @property
    def install_url(self):
        if not self.service_endpoint:
            return None
        return (
            settings.CYTOSCAPE_WEB_INSTALL_URL
            + quote(self.service_endpoint, safe="")
        )

    class Meta:
        ordering = ['-created']


class WEB_SUBMISSION_ORIGIN(models.TextChoices):
    WEB_URL = 'web_url', 'Web URL',
    WEB_BUNDLE = 'web_bundle', 'Web Bundle'

"""
class WebUrlStatus(models.TextChoices):
    PENDING_BUILD = 'pending_build', 'Pending Artifact Build',
    BUILD_FAILED = 'build_failed', 'Artifact Build Failed',
    PENDING_AUTO = 'pending_auto', 'Pending Automated Test',
    PENDING_REVIEW = 'pending_review', 'Pending Manual Review',
    PUBLISHED = 'published', 'Published',

class WebUrlRelease(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    version = models.CharField(max_length=31)
    status = models.CharField(max_length=31, choices=WebUrlStatus.choices)
    submitter = models.CharField(max_length=512, blank=True)
    #origin = models.CharField(max_length=31, choices=WEB_SUBMISSION_ORIGIN.choices)

    repo_url = models.URLField(blank=False, null=True)
    commit_ref = models.CharField(max_length=127, blank=False, null=True)


    resolved_commit_ref = models.CharField(max_length=127, blank=True, null=True)

    #for metadata from app-store.json
    federation_name = models.CharField(max_length=127, blank=True)
    exposed_module = models.CharField(max_length=127, blank=False, default="./AppConfig")
    install_command = models.CharField(max_length=255, default="npm ci")
    build_command = models.CharField(max_length=255, default="npm run build")
    output_dir = models.CharField(max_length=255, default="dist")
    raw_metadata = models.JSONField(default=dict, blank=True)

"""

class WebBundleRelease(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    # The app's Module Federation container name, taken verbatim from the
    # bundle's cy-manifest.json. Cytoscape Web compares this against the
    # CyApp.id inside the bundle and refuses the app if they differ, so it
    # cannot be derived from App.name: that is the store's URL slug, which is
    # case-folded and stripped of non-word characters.
    cy_app_id = models.CharField(max_length=128, blank=True, default='')
    version = models.CharField(max_length=31)
    author = models.CharField(max_length=127, blank=True)
    description = models.TextField(blank=True)
    license = models.CharField(max_length=64, blank=True)
    tags = models.JSONField(default=list, blank=True)
    icon = models.ImageField(upload_to=app_icon_path, blank=True,
                             null=True)
    citation = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)
    bundle = models.FileField(upload_to="webbundles/", null=True)

    created = models.DateTimeField(auto_now_add=True)
    bundle_hash = models.CharField(max_length=64)
    published_at = models.DateTimeField(auto_now_add=True)

    @property
    def bundle_path(self):
        return f"{self.app.name}/{self.version}/"

    @property
    def cdn_base_url(self):
        if not settings.CDN_BASE_URL:
            raise ImproperlyConfigured("CDN BASE URL must be set for this environment")
        return urljoin(settings.CDN_BASE_URL, self.bundle_path)

    @property
    def remote_entry_url(self):
        return urljoin(self.cdn_base_url, "remoteEntry.js")

    @property
    def manifest_url(self):
        return urljoin(self.cdn_base_url, "manifest.json")
    
    @property
    def created_iso(self):
        return self.created.isoformat()
    
    @property
    def install_url(self):
        return (
        settings.CYTOSCAPE_WEB_INSTALL_URL
        + quote(self.manifest_url, safe="")
    )

    class Meta:
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(fields=['app', 'version'], name="unique_web_bundle_release_version")
        ]
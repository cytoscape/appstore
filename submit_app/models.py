import subprocess
import datetime
from os.path import basename, join as pathjoin
from threading import Thread

from django.db import models
from django.contrib.auth.models import User
from apps.models import App, ServiceRelease, WebBundleRelease, Release, ReleaseAPI
from util.id_util import fullname_to_name
from util.view_util import get_object_or_none
from django.core.mail import send_mail
from django.core.files.storage import storages
from django.conf import settings
from submit_app.bundle_storage import write_manifest_json, _copy_bundle_to_storage
from urllib.parse import urljoin, quote


class AppPending(models.Model):
    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=127)
    version = models.CharField(max_length=31)
    cy_works_with = models.CharField(max_length=31)
    created = models.DateTimeField(auto_now_add=True)
    release_file = models.FileField(upload_to='pending_releases')
    dependencies = models.ManyToManyField(Release, related_name='+', blank=True)
    javadocs_jar_file = models.FileField(upload_to='pending_releases', blank=True, null=True)
    pom_xml_file = models.FileField(upload_to='pending_releases', blank=True, null=True)

    def can_confirm(self, user):
        if user.is_staff or user.is_superuser:
            return True
        return user.username == self.submitter.username

    @property
    def is_new_app(self):
       name = fullname_to_name(self.fullname)
       return get_object_or_none(App, name = name) == None

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.fullname + ' ' + self.version + ' from ' + self.submitter.email

    def make_release(self, app):
        release, _ = Release.objects.get_or_create(app = app, version = self.version)
        release.works_with = self.cy_works_with
        release.active = True
        release.created = datetime.datetime.today()
        release.save()
        release.release_file.save(basename(self.release_file.name), self.release_file)
        for dependee in self.dependencies.all():
            release.dependencies.add(dependee)
        release.calc_checksum()

        if not app.has_releases:
            app.has_releases = True
        app.latest_release_date = release.created
        app.save()

        if self.pom_xml_file and self.javadocs_jar_file:
            api, _ = ReleaseAPI.objects.get_or_create(release=release)
            api.javadocs_jar_file.save(basename(self.javadocs_jar_file.name), self.javadocs_jar_file)
            api.pom_xml_file.save(basename(self.pom_xml_file.name), self.pom_xml_file)
            api.save()
            api.extract_javadocs_jar()
            _deploy_artifact_async(api)

    def delete_files(self):
        self.release_file.delete()
        if self.javadocs_jar_file:
            self.javadocs_jar_file.delete()
        if self.pom_xml_file:
            self.pom_xml_file.delete()

def _deploy_artifact_async(api):
    def run_deploy():
        _deploy_artifact(api)
    t = Thread(target = run_deploy)
    t.start()

def _deploy_artifact(api):
    pom_path = pathjoin(settings.MEDIA_ROOT, api.pom_xml_file.name)
    jar_path = pathjoin(settings.MEDIA_ROOT, api.release.release_file.name)
    deploy_cmd = (settings.MVN_BIN_PATH,
        '-s', settings.MVN_SETTINGS_PATH,
        'deploy:deploy-file',
        '-Dpackaging=jar',
        '-Durl=http://code.cytoscape.org/nexus/content/repositories/apps',
        '-DpomFile=' + pom_path,
        '-Dfile=' + jar_path,
        '-DrepositoryId=apps')
    cmd = subprocess.Popen(deploy_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    cmdout, _ = cmd.communicate()
    send_mail('Cytoscape App Store - App Repo Deploy (Release API ID: %d)' % api.id, cmdout, settings.EMAIL_ADDR, settings.CONTACT_EMAILS, fail_silently=False)


class ServiceAppPending(models.Model):

    class Status(models.TextChoices):
        PENDING_CHECKER = 'pending_checker', 'Pending Checker' #submission was successful, waiting for checker command
        CHECKER_VALIDATED = 'checker_validated', 'Validated by Checker' #passed all checks from checker
        CHECKER_FAILED = 'checker_failed', 'Failed Checker' #checker validation failed
        PENDING_REVIEW = 'pending_review', 'Pending Manual Review' #checker passed, awaiting human/admin review

    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=127)
    version = models.CharField(max_length=31)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=31, choices=Status.choices, default=Status.PENDING_CHECKER)

    service_endpoint = models.URLField(blank=True, null=True)
    citation = models.CharField(max_length=512, blank=True)
    documentation = models.CharField(max_length=512, blank=True, null=True)

    author = models.CharField(max_length=512, blank=True, null=True)
    
    metadata = models.JSONField(null=True, blank=True)

    name = models.CharField(max_length=256, unique=True, db_index=True, null=True)

    class Meta:
        ordering = ['-created']
    
    def __str__(self):
        return f'{self.app.fullname} {self.version}'


    def make_service_release(self, app):
        release, _ = ServiceRelease.objects.get_or_create(app=app, version=self.version)
        release.service_endpoint = self.service_endpoint
        release.author = self.author or ''
        release.citation = self.citation or ''
        release.documentation = self.documentation or ''
        release.metadata = self.metadata
        release.active = True
        release.created = datetime.datetime.today()
        release.save()

        if not app.has_releases:
            app.has_releases = True
        app.latest_release_date = release.created
        app.save()


"""
class WebAppPending(models.Model):
    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=127)
    version = models.CharField(max_length=31)
    created = models.DateTimeField(auto_now_add=True)

    web_url = models.URLField(blank=False, null=True)
"""

class WebBundlePending(models.Model):
    class Status(models.TextChoices):
        DEFAULT = 'default_status', 'Default Status'
        PENDING_AUTOMATED_CHECKS = 'pending_automated_checks', 'Running Automated Checks'
        CHECKS_FAILED         = 'checks_failed', 'Automated Checks Failed'
        PENDING_REVIEW        = 'pending_review', 'Pending Manual Review'
        #PUBLISHED             = 'published', 'Published'
        #REJECTED              = 'rejected', 'Rejected'

    id = models.BigAutoField(primary_key=True)
    submitter = models.ForeignKey(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=128)
    author = models.CharField(max_length=512, blank=True)
    version = models.CharField(max_length=32)
    description = models.TextField(blank=True)
    license = models.CharField(max_length=64, blank=True)
    tags = models.JSONField(default=list, blank=True)
    icon = models.URLField(blank=True)


    #internal boundary
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DEFAULT)
    created = models.DateTimeField(auto_now_add=True)
    #remote_entry = models.FileField(upload_to="web_pending/", null=True)
    #remote_entry_hash = models.CharField(max_length=64)
    bundle = models.FileField(upload_to="web_pending/", null=True)
    bundle_hash = models.CharField(max_length=64)

    class Meta:
        ordering = ['-created']

    def delete_files(self):
        self.bundle.delete()
        web_storage = storages['web_bundles']
        for f in web_storage.listdir(self.bundle_path)[1]:
            web_storage.delete(f"{self.bundle_path}{f}")

    @property
    def bundle_path(self):
        return f"{self.fullname}/{self.version}/"

    @property
    def cdn_base_url(self):
        return urljoin(settings.CDN_BASE_URL, self.bundle_path)

    @property
    def remote_entry_url(self):
        return urljoin(self.cdn_base_url, "remoteEntry.js")

    @property
    def manifest_url(self):
        return urljoin(self.cdn_base_url, "manifest.json")
    
    @property
    def install_url(self):
        return (
        "https://dev1.ndexbio.org/cytoscape/?installApp="
        + quote(self.manifest_url, safe="")
    )

    def make_bundle_release(self, app: "App") -> "WebBundleRelease":
        #cdn_base_url = urljoin(settings.CDN_BASE_URL, f"{app.name}/{self.version}/")

        release, _ = WebBundleRelease.objects.get_or_create(app=app, version=self.version)

        release.author = self.author
        release.description = self.description
        release.license = self.license
        release.tags = self.tags
        #release.remote_entry_hash = self.remote_entry_hash
        release.bundle_hash = self.bundle_hash
        release.active = True
        release.save()

        if not app.has_releases:
            app.has_releases = True

        app.latest_release_date = release.created
        _copy_bundle_to_storage(self.bundle, destination=f"{app.name}/{self.version}/")
        write_manifest_json(release)
        app.save()
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from apps.models import App, Release, ReleaseAPI
from util.id_util import fullname_to_name
from util.view_util import get_object_or_none
from os.path import basename, join as pathjoin
from threading import Thread
import subprocess
import datetime
from django.core.mail import send_mail
import warnings
try:
    from conf.mvn import MVN_BIN_PATH, MVN_SETTINGS_PATH
    from conf.emails import EMAIL_ADDR
except ImportError:
    from conf.mock import MVN_BIN_PATH, MVN_SETTINGS_PATH, EMAIL_ADDR

class AppPending(models.Model):
    submitter     = models.ForeignKey(User)
    fullname      = models.CharField(max_length=127)
    version       = models.CharField(max_length=31)
    cy_works_with = models.CharField(max_length=31)
    created       = models.DateTimeField(auto_now_add=True)
    release_file  = models.FileField(upload_to='pending_releases')
    dependencies  = models.ManyToManyField(Release, related_name='+', blank=True, null=True)
    javadocs_jar_file = models.FileField(upload_to='pending_releases', blank=True, null=True)
    pom_xml_file      = models.FileField(upload_to='pending_releases', blank=True, null=True)

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
            api, _ = ReleaseAPI.objects.get_or_create(release = release)
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
    deploy_cmd = (MVN_BIN_PATH,
        '-s', MVN_SETTINGS_PATH,
        'deploy:deploy-file',
        '-Dpackaging=jar',
        '-Durl=http://code.cytoscape.org/nexus/content/repositories/apps',
        '-DpomFile=' + pom_path,
        '-Dfile=' + jar_path,
        '-DrepositoryId=apps')
    cmd = subprocess.Popen(deploy_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
    cmdout, _ = cmd.communicate()
    send_mail('Cytoscape App Store - App Repo Deploy (Release API ID: %d)' % api.id, cmdout, EMAIL_ADDR, settings.CONTACT_EMAILS, fail_silently=False)

import json
import os

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from apps.models import App, Platform, Release, ServiceRelease, WebBundleRelease
from submit_app.bundle_storage import write_manifest_json
from submit_app.models import AppPending, ServiceAppPending, WebBundlePending, WebUrlPending
from util.id_util import fullname_to_name

USERS = {
    'admin': {'username': 'it-admin', 'email': 'it-admin@example.org', 'is_staff': True, 'is_superuser': True},
    'editor': {'username': 'it-editor', 'email': 'it-editor@example.org'},
    'other': {'username': 'it-other', 'email': 'it-other@example.org'},
}


def sessions_file():
    return os.path.join(settings.BUILD_DIR, 'it_sessions.json')


class Command(BaseCommand):
    help = ('Replaces all apps, pending submissions and it-* users with the integration test data, '
            'and writes a logged-in session key per test user to build/it_sessions.json. '
            'Runs only where settings.INTEGRATION_SEED_ENABLED is True.')

    def handle(self, *args, **options):
        if not getattr(settings, 'INTEGRATION_SEED_ENABLED', False):
            raise CommandError('seed_integration_data deletes all apps; it runs only with INTEGRATION_SEED_ENABLED')

        self.flush()
        users = {role: self.create_user(**fields) for role, fields in USERS.items()}
        self.create_apps(users)

        sessions = {role: self.create_session(user) for role, user in users.items()}
        os.makedirs(os.path.dirname(sessions_file()), exist_ok=True)
        with open(sessions_file(), 'w') as f:
            json.dump(sessions, f, indent=2)
        self.stdout.write('Seeded integration data; sessions in %s' % sessions_file())

    def flush(self):
        for model in (AppPending, ServiceAppPending, WebBundlePending, WebUrlPending):
            model.objects.all().delete()
        App.objects.all().delete()
        User.objects.filter(username__in=[u['username'] for u in USERS.values()]).delete()

    def create_user(self, username, email, is_staff=False, is_superuser=False):
        return User.objects.create_user(username=username, email=email, password=None,
                                        is_staff=is_staff, is_superuser=is_superuser)

    def create_session(self, user):
        session = SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.ModelBackend'
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.create()
        return session.session_key

    def create_app(self, fullname, platform, editor, **fields):
        app = App.objects.create(name=fullname_to_name(fullname), fullname=fullname,
                                 platform=platform, active=True,
                                 description='%s, seeded for the integration tests' % fullname, **fields)
        app.editors.add(editor)
        return app

    def create_apps(self, users):
        editor = users['editor']

        desktop = self.create_app('IT Desktop', Platform.DESKTOP, editor, has_releases=True)
        release = Release.objects.create(app=desktop, version='1.0', works_with='3.10')
        release.release_file.save('itdesktop-1.0.jar', ContentFile(b'integration test jar'))
        release.calc_checksum()
        self.mark_released(desktop, release)

        web = self.create_app('IT Web', Platform.WEB, editor, has_releases=True)
        web_release = WebBundleRelease.objects.create(app=web, version='1.0', cy_app_id='itweb',
                                                      active=True, bundle_hash='0' * 64)
        write_manifest_json(web_release)
        self.mark_released(web, web_release)

        service = self.create_app('IT Service', Platform.SERVICE, editor, has_releases=True)
        service_release = ServiceRelease.objects.create(
            app=service, version='1.0', service_endpoint='https://service.example.org/itservice',
            metadata={'name': 'IT Service', 'version': '1.0'})
        self.mark_released(service, service_release)

        self.create_app('IT Legacy', Platform.DESKTOP, editor,
                        cy_2x_plugin_download='https://example.org/itlegacy-1.0.jar',
                        cy_2x_plugin_version='1.0', cy_2x_versions='2.8')

    def mark_released(self, app, release):
        app.latest_release_date = release.created
        app.save()

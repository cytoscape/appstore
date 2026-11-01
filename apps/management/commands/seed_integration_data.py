import io
import json
import os
import zipfile

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from apps.models import App, Release, ServiceRelease, WebBundleRelease
from submit_app.bundle_storage import _copy_bundle_to_storage, write_manifest_json, write_pending_manifest_json
from submit_app.models import AppPending, ServiceAppPending, WebBundlePending, WebUrlPending
from util.id_util import fullname_to_name

USERS = {
    'admin': {'username': 'it-admin', 'email': 'it-admin@example.org', 'is_staff': True, 'is_superuser': True},
    'editor': {'username': 'it-editor', 'email': 'it-editor@example.org'},
    'other': {'username': 'it-other', 'email': 'it-other@example.org'},
}


def sessions_file():
    return os.path.join(settings.BUILD_DIR, 'it_sessions.json')


# Specs that change data own the seeded objects they change, so the specs stay independent:
# admin-accept.spec.ts accepts IT Desktop's pending Cytoscape Web bundle, and
# admin-queue.spec.ts declines IT Url App, and tiles-edit.spec.ts edits IT Edit.
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
        self.create_pending(users)

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

    def create_app(self, fullname, editor, **fields):
        app = App.objects.create(name=fullname_to_name(fullname), fullname=fullname, active=True,
                                 description='%s, seeded for the integration tests' % fullname, **fields)
        app.editors.add(editor)
        return app

    def create_apps(self, users):
        editor = users['editor']

        desktop = self.create_app('IT Desktop', editor, has_releases=True)
        release = Release.objects.create(app=desktop, version='1.0', works_with='3.10')
        release.release_file.save('itdesktop-1.0.jar', ContentFile(b'integration test jar'))
        release.calc_checksum()
        self.mark_released(desktop, release)

        web = self.create_app('IT Web', editor, has_releases=True)
        web_release = WebBundleRelease.objects.create(app=web, version='1.0', cy_app_id='itweb',
                                                      active=True, bundle_hash='0' * 64)
        write_manifest_json(web_release)
        self.mark_released(web, web_release)

        service = self.create_app('IT Service', editor, has_releases=True)
        service_release = ServiceRelease.objects.create(
            app=service, version='1.0', service_endpoint='https://service.example.org/itservice',
            metadata={'name': 'IT Service', 'version': '1.0'})
        self.mark_released(service, service_release)

        # the same version on all three platforms
        multi = self.create_app('IT Multi', editor, has_releases=True)
        multi_desktop = Release.objects.create(app=multi, version='1.0', works_with='3.10')
        multi_desktop.release_file.save('itmulti-1.0.jar', ContentFile(b'integration test jar'))
        multi_desktop.calc_checksum()
        write_manifest_json(WebBundleRelease.objects.create(app=multi, version='1.0', cy_app_id='itmulti',
                                                            active=True, bundle_hash='0' * 64))
        ServiceRelease.objects.create(app=multi, version='1.0', service_endpoint='https://service.example.org/itmulti',
                                      metadata={'name': 'IT Multi', 'version': '1.0'})
        self.mark_released(multi, multi_desktop)

        # edited by tiles-edit.spec.ts, so it has all three platforms of its own
        edited = self.create_app('IT Edit', editor, has_releases=True)
        edited_desktop = Release.objects.create(app=edited, version='1.0', works_with='3.10')
        write_manifest_json(WebBundleRelease.objects.create(app=edited, version='1.0', cy_app_id='itedit',
                                                            active=True, bundle_hash='0' * 64))
        ServiceRelease.objects.create(app=edited, version='1.0', service_endpoint='https://service.example.org/itedit',
                                      metadata={'name': 'IT Edit', 'version': '1.0'})
        self.mark_released(edited, edited_desktop)

        self.create_app('IT Legacy', editor,
                        cy_2x_plugin_download='https://example.org/itlegacy-1.0.jar',
                        cy_2x_plugin_version='1.0', cy_2x_versions='2.8')

    def create_pending(self, users):
        # IT Desktop's editor submitted a Cytoscape Web version, which awaits review
        web_pending = WebBundlePending.objects.create(
            submitter=users['editor'], fullname='IT Desktop', cy_app_id='itdesktop', version='1.0',
            author='it-editor', bundle_hash='1' * 64, status=WebBundlePending.Status.PENDING_REVIEW)
        web_pending.bundle.save('itdesktop-1.0.zip', ContentFile(self.web_bundle('itdesktop', 'IT Desktop', '1.0')))
        _copy_bundle_to_storage(web_pending.bundle, web_pending.bundle_path)
        write_pending_manifest_json(web_pending)

        # the admin queue's three kinds of row: a new app, a new platform, and a GitHub-URL web app
        new_app = AppPending.objects.create(submitter=users['other'], fullname='IT Brand New',
                                            version='1.0', cy_works_with='3.10')
        new_app.release_file.save('itbrandnew-1.0.jar', ContentFile(b'integration test jar'))
        ServiceAppPending.objects.create(
            submitter=users['editor'], fullname='IT Desktop', name='itdesktop', version='1.0', author='it-editor',
            service_endpoint='https://service.example.org/itdesktop',
            status=ServiceAppPending.Status.PENDING_REVIEW)
        WebUrlPending.objects.create(submitter=users['other'], fullname='IT Url App', version='1.0',
                                     repo_url='https://github.com/cytoscape/it-url-app')

    def web_bundle(self, cy_app_id, fullname, version):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as zf:
            zf.writestr('dist/remoteEntry.js', 'var %s;' % cy_app_id)
            zf.writestr('dist/cy-manifest.json', json.dumps({'id': cy_app_id, 'name': fullname, 'version': version}))
        return data.getvalue()

    def mark_released(self, app, release):
        app.latest_release_date = release.created
        app.save()

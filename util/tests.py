"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import io
import os
import tempfile
import shutil
import subprocess
from unittest.mock import patch
import yaml
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from util.img_util import *
from util.id_util import AppIdentity, IdentityOutcome, resolve_app_identity
from util import version
from apps.models import App, Platform, Release


def image_to_byte_array(img, img_format):
    img_b_arr = io.BytesIO()
    img.save(img_b_arr, format=img_format)
    return img_b_arr.getvalue()


class ImgUtilTestCase(TestCase):

    def test_scale_img_with_none_passed_in_as_file(self):
        try:
            scale_img(None, 'foo', 100)
            self.fail('Expected ValueError')
        except ValueError as ve:
            self.assertEqual("invalid image file: 'NoneType' "
                             "object has no attribute 'read'", str(ve))

    def test_scale_img_with_image_that_does_not_need_scale(self):
        test_img = Image.new('RGB', (100, 200))
        f = SimpleUploadedFile('foo',
                               image_to_byte_array(test_img, 'PNG'),
                               content_type="image/png")
        res = scale_img(f, 'hello', max_px=300,
                        scale_on_height=False)
        self.assertEqual(res, f)
        res = scale_img(f, 'hello', max_px=300,
                        scale_on_height=True)
        self.assertEqual(res, f)

    def test_scale_img_with_tall_image(self):
        test_img = Image.new('RGB', (100, 200))
        f = SimpleUploadedFile('foo',
                               image_to_byte_array(test_img, 'PNG'),
                               content_type="image/png")
        res = scale_img(f, 'hello', max_px=100,
                        scale_on_height=False)
        self.assertNotEqual(res, f)
        res_img = Image.open(res)
        self.assertEqual(50, res_img.size[0])
        self.assertEqual(100, res_img.size[1])

        res = scale_img(f, 'hello', max_px=50,
                        scale_on_height=True)
        self.assertNotEqual(res, f)
        res_img = Image.open(res)
        self.assertEqual(25, res_img.size[0])
        self.assertEqual(50, res_img.size[1])

    def test_scale_img_with_wide_image(self):
        test_img = Image.new('RGB', (200, 100))
        f = SimpleUploadedFile('foo',
                               image_to_byte_array(test_img, 'PNG'),
                               content_type="image/png")
        res = scale_img(f, 'hello', max_px=100,
                        scale_on_height=False)
        self.assertNotEqual(res, f)
        res_img = Image.open(res)
        self.assertEqual(100, res_img.size[0])
        self.assertEqual(50, res_img.size[1])

        res = scale_img(f, 'hello', max_px=50,
                        scale_on_height=True)
        self.assertNotEqual(res, f)
        res_img = Image.open(res)
        self.assertEqual(100, res_img.size[0])
        self.assertEqual(50, res_img.size[1])


class CiWorkflowTestCase(TestCase):
    """Pull requests must run the same make targets as the local gate: make test and make integration-test."""

    def setUp(self):
        with open(os.path.join(settings.BASE_DIR, '.github', 'workflows', 'ci.yml')) as f:
            self.workflow = yaml.safe_load(f)

    def runs(self, job):
        return [step.get('run', '') for step in self.workflow['jobs'][job]['steps']]

    def job_running(self, command):
        jobs = [name for name in self.workflow['jobs'] if any(command == run.strip() for run in self.runs(name))]
        self.assertEqual(1, len(jobs), 'expected one job running %r' % command)
        return jobs[0]

    def assert_runs_after(self, job, earlier, later):
        runs = self.runs(job)
        earlier_at = next(i for i, run in enumerate(runs) if earlier in run)
        later_at = next(i for i, run in enumerate(runs) if run.strip() == later)
        self.assertLess(earlier_at, later_at)

    def test_triggers_on_pull_requests(self):
        # YAML 1.1 reads the bare key "on" as True
        triggers = self.workflow.get('on', self.workflow.get(True))
        self.assertIn('pull_request', triggers)

    def test_a_job_runs_make_test_after_chromium_libraries(self):
        job = self.job_running('make test')
        self.assert_runs_after(job, 'playwright install-deps chromium', 'make test')

    def test_a_job_runs_make_integration_test_after_browser_libraries(self):
        job = self.job_running('make integration-test')
        self.assert_runs_after(job, 'playwright install-deps chromium firefox', 'make integration-test')


class ResolveAppIdentityTestCase(TestCase):
    """A submission's name picks its app regardless of platform."""

    def setUp(self):
        self.editor = User.objects.create_user('editor', 'editor@example.org', 'secret')
        self.other = User.objects.create_user('other', 'other@example.org', 'secret')
        self.staff = User.objects.create_user('staff', 'staff@example.org', 'secret', is_staff=True)
        self.app = App.objects.create(name='foo', fullname='Foo', active=True)
        self.app.editors.add(self.editor)
        Release.objects.create(app=self.app, version='1.0', works_with='3.10')

    def test_unknown_name_is_a_new_app(self):
        identity = resolve_app_identity('Brand New', self.other, Platform.WEB)
        self.assertEqual(AppIdentity('brandnew', None, IdentityOutcome.NEW_APP), identity)

    def test_editor_on_a_platform_the_app_has(self):
        identity = resolve_app_identity('Foo', self.editor, Platform.DESKTOP)
        self.assertEqual(self.app, identity.app)
        self.assertEqual(IdentityOutcome.EXISTING_PLATFORM, identity.outcome)

    def test_editor_on_a_new_platform(self):
        identity = resolve_app_identity('Foo', self.editor, Platform.SERVICE)
        self.assertEqual(self.app, identity.app)
        self.assertEqual(IdentityOutcome.NEW_PLATFORM, identity.outcome)

    def test_non_editor_cannot_take_the_name_on_any_platform(self):
        for platform in Platform:
            self.assertEqual(IdentityOutcome.NOT_EDITOR,
                             resolve_app_identity('Foo', self.other, platform).outcome)

    def test_staff_count_as_editors(self):
        self.assertEqual(IdentityOutcome.NEW_PLATFORM,
                         resolve_app_identity('Foo', self.staff, Platform.WEB).outcome)

    def test_case_and_punctuation_variants_are_the_same_app(self):
        for variant in ('FOO', 'foo', 'F-o-o', 'F o o'):
            identity = resolve_app_identity(variant, self.editor, Platform.WEB)
            self.assertEqual(('foo', IdentityOutcome.NEW_PLATFORM), (identity.name, identity.outcome))
            self.assertEqual('Foo', identity.app.fullname)

    def test_inactive_app_still_holds_its_name(self):
        App.objects.filter(pk=self.app.pk).update(active=False)
        self.assertEqual(IdentityOutcome.NOT_EDITOR,
                         resolve_app_identity('Foo', self.other, Platform.WEB).outcome)


class IntegrationContainerTestCase(TestCase):
    """The integration-test container runs Django's debug server, so only this machine may reach it."""

    def test_container_port_is_published_on_localhost_only(self):
        with open(os.path.join(settings.BASE_DIR, 'docker', 'integration-test.sh')) as f:
            script = f.read()
        self.assertIn('-p "127.0.0.1:$PORT:8000"', script)
        self.assertNotIn('-p "$PORT:8000"', script)


class AppVersionTestCase(TestCase):
    """The footer's version comes from git: the tag at HEAD, else HEAD's short hash, else 'develop'."""

    def setUp(self):
        version.app_version.cache_clear()

    def tearDown(self):
        version.app_version.cache_clear()

    @staticmethod
    def git(results):
        """A stand-in for subprocess.run answering each git command from 'results' (by its first argument)."""
        calls = []

        def run(args, **kwargs):
            calls.append(args[1])
            result = results[args[1]]
            if isinstance(result, BaseException):
                raise result
            returncode, stdout = result
            return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr='')
        return run, calls

    def test_tag_at_head(self):
        run, calls = self.git({'describe': (0, '2.1.0\n'), 'rev-parse': (0, 'b27ca14\n')})
        with patch.object(version.subprocess, 'run', run):
            self.assertEqual('2.1.0', version.app_version())
        self.assertEqual(['describe'], calls)

    def test_short_hash_without_a_tag(self):
        run, calls = self.git({'describe': (128, ''), 'rev-parse': (0, 'b27ca14\n')})
        with patch.object(version.subprocess, 'run', run):
            self.assertEqual('b27ca14', version.app_version())
        self.assertEqual(['describe', 'rev-parse'], calls)

    def test_develop_when_git_fails(self):
        for name, results in (
                ('git not installed', {'describe': FileNotFoundError('git'), 'rev-parse': FileNotFoundError('git')}),
                ('not a repository', {'describe': (128, ''), 'rev-parse': (128, '')}),
                ('timeout', {'describe': subprocess.TimeoutExpired('git', 5), 'rev-parse': subprocess.TimeoutExpired('git', 5)}),
                ('empty output', {'describe': (0, ''), 'rev-parse': (0, '  \n')})):
            version.app_version.cache_clear()
            run, _ = self.git(results)
            with patch.object(version.subprocess, 'run', run):
                self.assertEqual('develop', version.app_version(), name)

    def test_worked_out_once(self):
        run, calls = self.git({'describe': (0, '2.1.0\n')})
        with patch.object(version.subprocess, 'run', run):
            version.app_version()
            version.app_version()
        self.assertEqual(['describe'], calls)

    def test_footer_shows_it_after_contact_us(self):
        run, _ = self.git({'describe': (0, '2.1.0\n')})
        with patch.object(version.subprocess, 'run', run):
            content = self.client.get('/apps/').content.decode('utf-8')
        footer = content[content.index('<footer'):content.index('</footer>')]
        self.assertIn('<span id="cy-app-version">Version: 2.1.0</span>', footer)
        self.assertLess(footer.index('Contact Us'), footer.index('Version: 2.1.0'))
        self.assertLess(footer.index('Version: 2.1.0'), footer.index('Wall of Apps'))

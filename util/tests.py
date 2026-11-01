"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import io
import os
import tempfile
import shutil
import yaml
from django.conf import settings
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from util.img_util import *


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

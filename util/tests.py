"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import io
import os
import tempfile
import shutil
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

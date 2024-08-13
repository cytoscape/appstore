from django.core.files import File
from PIL import Image

from io import BytesIO


def scale_img(f, name, max_px, scale_on_height=False):
    """
    Rescales image pointed to by 'f' file path if necessary.

    :param f: image file to rescale
    :param name: name of file
    :param max_px: maximum pixels to allow
    :param scale_on_height: If `None` or `False` scale image if either
                            width or height exceed 'max_px' such that
                            'max_px' equals the larger of the two values,
                            otherwise only scale down if height exceeds 'max_px'
                            so that height is set to 'max_px'
    :type scale_on_height: bool
    :raises: ValueError if any parameter is invalid
    :return: 'f' if no scaling needed otherwise new :py:class:`django.core.files.File`
             containing scaled image
    """
    try:
        img = Image.open(f, 'r')
    except AttributeError as ae:
        raise ValueError('invalid image file: ' + str(ae))
    except IOError:
        raise ValueError('invalid image file')
    (w, h) = img.size

    if scale_on_height is None or scale_on_height is False:
        return _scale_img(f, name, img, w, h, max_px)

    return _scale_img_height(f, name, img, w, h, max_px)


def _scale_img(f, name, img, w, h, max_px):
    """
    Scales down image if 'w' or 'h' exceeds 'max_px' so
    that the larger dimension is value of 'max_px'

    :param f: file for image
    :param name: name of image
    :param img: loaded image
    :type img: :py:class:`PIL.Image`
    :param w: width of image in pixels
    :param h: height of image in pixels
    :param max_px: maximum pixels allowed in width or height
    :return: 'f' or :py:class:`django.core.files.File`
             containing scaled image
    """
    if w > max_px or h > max_px:
        if w > h:
            h = max_px * h / w
            w = max_px
        else:
            w = max_px * w / h
            h = max_px
        return _scale_img_to_new_sizes(name, img, w, h)
    return f


def _scale_img_height(f, name, img, w, h, max_px):
    """
    Scales down image if 'h' exceeds 'max_px' so
    that the larger dimension is value of 'max_px'

    :param f: file for image
    :param name: name of image
    :param img: loaded image
    :type img: :py:class:`PIL.Image`
    :param w: width of image in pixels
    :param h: height of image in pixels
    :param max_px: maximum pixels allowed in width or height
    :return: 'f' or :py:class:`django.core.files.File`
             containing scaled image
    """
    if h > max_px:
        w = max_px * w / h
        h = max_px
        return _scale_img_to_new_sizes(name, img, w, h)
    return f


def _scale_img_to_new_sizes(name, img, w, h):
    """
    Resizes 'img' to width 'w' and height 'h' specified
    saving to file with name set to 'name' with '.png'
    which converts the output image to PNG format

    :param name: name of image which will have '.png' appended
                 to it
    :param img: loaded image
    :type img: :py:class:`PIL.Image`
    :param w: desired width of rescaled image in pixels
    :param h: desired height of rescaled image in pixels
    :return: image as file object
    :rtype: :py:class:`django.core.files.File`
    """
    scaled_img = img.resize((int(w), int(h)), Image.Resampling.LANCZOS)
    scaled_buffer = BytesIO()
    scaled_img.save(scaled_buffer, 'PNG')
    return File(scaled_buffer, name=name + '.png')

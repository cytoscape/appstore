from django.core.files import File
from PIL import Image
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
def scale_img(f, name, max_px, dim):
    try:
        img = Image.open(f, 'r')
    except IOError:
        raise ValueError('invalid image file')
    (w, h) = img.size

    if dim == 'h':
        if h > max_px:
            w = max_px * w / h
            h = max_px
        else:
            return f
    elif dim == 'both':
        if w > max_px or h > max_px:
            if w > h:
                h = max_px * h / w
                w = max_px
            else:
                w = max_px * w / h
                h = max_px
        else:
            return f

    scaled_img = img.resize((w, h), Image.ANTIALIAS)
    scaled_buffer = BytesIO()
    scaled_img.save(scaled_buffer, 'PNG')
    scaled_f = File(scaled_buffer, name = name + '.png')
    scaled_f._set_size(len(scaled_buffer.getvalue()))
    return scaled_f

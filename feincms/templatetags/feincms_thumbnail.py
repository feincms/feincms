import os
from cStringIO import StringIO
try:
    from PIL import Image
except ImportError:
    # Django seems to silently swallow the ImportError under certain
    # circumstances. Raise a generic exception explaining why we are
    # unable to proceed.
    raise Exception, 'FeinCMS requires PIL to be installed'

from django import template
from django.conf import settings
from django.utils.encoding import force_unicode
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


register = template.Library()


def tryint(v):
    try:
        return int(v)
    except ValueError:
        return 999999 # Arbitrarily big number


@register.filter
def thumbnail(filename, size='200x200'):
    """
    Creates a thumbnail from the image passed, returning its path::

        {{ object.image|thumbnail:"400x300" }}
    OR
        {{ object.image.name|thumbnail:"400x300" }}

    You can pass either an ``ImageField``, ``FileField`` or the ``name``
    but not the ``url`` attribute of an ``ImageField`` or ``FileField``.

    The dimensions passed are treated as a bounding box. The aspect ratio of
    the initial image is preserved. Images aren't blown up in size if they
    are already smaller.

    Both width and height must be specified. If you do not care about one
    of them, just set it to an arbitrarily large number::

        {{ object.image|thumbnail:"300x999999" }}
    """

    if not (filename and 'x' in size):
        # Better return empty than crash
        return u''

    # figure out storage
    if hasattr(filename, 'storage'):
        storage = filename.storage
    else:
        storage = default_storage

    # figure out name
    if hasattr(filename, 'name'):
        filename = filename.name
    else:
        filename = force_unicode(filename)

    # defining the size
    x, y = [tryint(x) for x in size.split('x')]
    # defining the filename and the miniature filename
    try:
        basename, format = filename.rsplit('.', 1)
    except ValueError:
        basename, format = filename, 'jpg'
    miniature = basename + '_thumb_' + size + '.' +  format

    if not storage.exists(miniature):
        generate = True
    else:
        try:
            generate = storage.modified_time(miniature)<storage.modified_time(filename)
        except (NotImplementedError, AttributeError):
            # storage does NOT support modified_time
            generate = False

    if generate:
        image = Image.open(StringIO(storage.open(filename).read()))
        image.thumbnail([x, y], Image.ANTIALIAS)
        buf = StringIO()
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        image.save(buf, image.format or 'jpeg', quality=100)
        raw_data = buf.getvalue()
        buf.close()
        storage.save(miniature, ContentFile(raw_data))

    return storage.url(miniature)

@register.filter
def cropscale(filename, size='200x200'):
    """
    Scales the image down and crops it so that its size equals exactly the size
    passed (as long as the initial image is bigger than the specification).
    """

    if not (filename and 'x' in size):
        # Better return empty than crash
        return u''

    # figure out storage
    if hasattr(filename, 'storage'):
        storage = filename.storage
    else:
        storage = default_storage

    # figure out name
    if hasattr(filename, 'name'):
        filename = filename.name
    else:
        filename = force_unicode(filename)

    w, h = [tryint(x) for x in size.split('x')]

    try:
        basename, format = filename.rsplit('.', 1)
    except ValueError:
        basename, format = filename, 'jpg'
    miniature = basename + '_cropscale_' + size + '.' +  format

    if not storage.exists(miniature):
        generate = True
    else:
        try:
            generate = storage.modified_time(miniature)<storage.modified_time(filename)
        except (NotImplementedError, AttributeError):
            # storage does NOT support modified_time
            generate = False

    if generate:
        image = Image.open(StringIO(storage.open(filename).read()))
        src_width, src_height = image.size
        src_ratio = float(src_width) / float(src_height)
        dst_width, dst_height = w, h
        dst_ratio = float(dst_width) / float(dst_height)

        if dst_ratio < src_ratio:
            crop_height = src_height
            crop_width = crop_height * dst_ratio
            x_offset = float(src_width - crop_width) / 2
            y_offset = 0
        else:
            crop_width = src_width
            crop_height = crop_width / dst_ratio
            x_offset = 0
            y_offset = float(src_height - crop_height) / 2

        image = image.crop((x_offset, y_offset, x_offset+int(crop_width), y_offset+int(crop_height)))
        image = image.resize((dst_width, dst_height), Image.ANTIALIAS)

        buf = StringIO()
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        image.save(buf, image.format or 'jpeg', quality=100)
        raw_data = buf.getvalue()
        buf.close()
        storage.save(miniature, ContentFile(raw_data))

    return storage.url(miniature)

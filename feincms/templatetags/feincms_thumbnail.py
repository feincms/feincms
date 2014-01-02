# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from io import BytesIO
import re

# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        # Django seems to silently swallow the ImportError under certain
        # circumstances. Raise a generic exception explaining why we are
        # unable to proceed.
        raise Exception('FeinCMS requires PIL to be installed')

from django import template
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import six

from feincms import settings


register = template.Library()


@python_2_unicode_compatible
class Thumbnailer(object):
    THUMBNAIL_SIZE_RE = re.compile(r'^(?P<w>\d+)x(?P<h>\d+)$')
    MARKER = '_thumb_'

    def __init__(self, filename, size='200x200'):
        self.filename = filename
        self.size = size

    @property
    def url(self):
        return six.text_type(self)

    def __str__(self):
        match = self.THUMBNAIL_SIZE_RE.match(self.size)
        if not (self.filename and match):
            return ''

        matches = match.groupdict()

        # figure out storage
        if hasattr(self.filename, 'storage'):
            storage = self.filename.storage
        else:
            storage = default_storage

        # figure out name
        if hasattr(self.filename, 'name'):
            filename = self.filename.name
        else:
            filename = force_text(self.filename)

        # defining the filename and the miniature filename
        try:
            basename, format = filename.rsplit('.', 1)
        except ValueError:
            basename, format = filename, 'jpg'

        miniature = ''.join([
            settings.FEINCMS_THUMBNAIL_DIR,
            basename,
            self.MARKER,
            self.size,
            '.',
            format,
        ])

        if not storage.exists(miniature):
            generate = True
        else:
            try:
                generate = (
                    storage.modified_time(miniature)
                    < storage.modified_time(filename))
            except (NotImplementedError, AttributeError):
                # storage does NOT support modified_time
                generate = False
            except (OSError, IOError):
                # Someone might have delete the file
                return ''

        if generate:
            return self.generate(
                storage=storage,
                original=filename,
                size=matches,
                miniature=miniature)

        return storage.url(miniature)

    def generate(self, storage, original, size, miniature):
        try:
            image = Image.open(BytesIO(storage.open(original).read()))

            # defining the size
            w, h = int(size['w']), int(size['h'])

            format = image.format  # Save format for the save() call later
            image.thumbnail([w, h], Image.ANTIALIAS)
            buf = BytesIO()
            if image.mode not in ('RGBA', 'RGB', 'L'):
                image = image.convert('RGBA')
            image.save(
                buf,
                format if format.lower() in ('jpg', 'jpeg', 'png') else 'jpeg',
                quality=90)
            raw_data = buf.getvalue()
            buf.close()

            storage.delete(miniature)
            storage.save(miniature, ContentFile(raw_data))

            return storage.url(miniature)
        except:
            # PIL raises a plethora of Exceptions if reading the image
            # is not possible. Since we cannot be sure what Exception will
            # happen, catch them all so the thumbnailer will never fail.
            return storage.url(original)


class CropscaleThumbnailer(Thumbnailer):
    THUMBNAIL_SIZE_RE = re.compile(
        r'^(?P<w>\d+)x(?P<h>\d+)(-(?P<x>\d+)x(?P<y>\d+))?$')
    MARKER = '_cropscale_'

    def generate(self, storage, original, size, miniature):
        try:
            image = Image.open(BytesIO(storage.open(original).read()))
        except:
            # PIL raises a plethora of Exceptions if reading the image
            # is not possible. Since we cannot be sure what Exception will
            # happen, catch them all so the thumbnailer will never fail.
            return storage.url(original)

        storage.delete(miniature)

        w, h = int(size['w']), int(size['h'])

        if size['x'] and size['y']:
            x, y = int(size['x']), int(size['y'])
        else:
            x, y = 50, 50

        src_width, src_height = image.size
        src_ratio = float(src_width) / float(src_height)
        dst_width, dst_height = w, h
        dst_ratio = float(dst_width) / float(dst_height)

        if dst_ratio < src_ratio:
            crop_height = src_height
            crop_width = crop_height * dst_ratio
            x_offset = int(float(src_width - crop_width) * x / 100)
            y_offset = 0
        else:
            crop_width = src_width
            crop_height = crop_width / dst_ratio
            x_offset = 0
            y_offset = int(float(src_height - crop_height) * y / 100)

        format = image.format  # Save format for the save() call later
        image = image.crop((
            x_offset,
            y_offset,
            x_offset + int(crop_width),
            y_offset + int(crop_height)))
        image = image.resize((dst_width, dst_height), Image.ANTIALIAS)

        buf = BytesIO()
        if image.mode not in ('RGBA', 'RGB', 'L'):
            image = image.convert('RGBA')
        image.save(
            buf,
            format if format.lower() in ('jpg', 'jpeg', 'png') else 'jpeg',
            quality=90)
        raw_data = buf.getvalue()
        buf.close()
        storage.save(miniature, ContentFile(raw_data))

        return storage.url(miniature)


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

    return Thumbnailer(filename, size)


@register.filter
def cropscale(filename, size='200x200'):
    """
    Scales the image down and crops it so that its size equals exactly the size
    passed (as long as the initial image is bigger than the specification).
    """

    return CropscaleThumbnailer(filename, size)

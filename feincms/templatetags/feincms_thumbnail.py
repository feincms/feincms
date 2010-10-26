from random import random
import os
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


register = template.Library()


def tryint(v):
    try:
        return int(v)
    except ValueError:
        return 999999 # Arbitrarily big number


@register.filter
def thumbnail(filename, size='200x200'):
    if not (filename and 'x' in size):
        # Better return empty than crash
        return u''

    # defining the size
    x, y = [tryint(x) for x in size.split('x')]
    # defining the filename and the miniature filename
    try:
        basename, format = filename.rsplit('.', 1)
    except ValueError:
        basename, format = filename, 'jpg'
    miniature = basename + '_thumb_' + size + '.' +  format
    miniature_filename = os.path.join(settings.MEDIA_ROOT, miniature).encode('utf-8')
    miniature_url = os.path.join(settings.MEDIA_URL, miniature).encode('utf-8')
    orig_filename = os.path.join(settings.MEDIA_ROOT, filename).encode('utf-8')
    # if the image wasn't already resized, resize it
    if not os.path.exists(miniature_filename) or (os.path.getmtime(miniature_filename)<os.path.getmtime(orig_filename)):
        try:
            image = Image.open(orig_filename)
            image.thumbnail([x, y], Image.ANTIALIAS)
            image.save(miniature_filename, image.format, quality=100)
        except IOError:
            return os.path.join(settings.MEDIA_URL, filename)
    return force_unicode(miniature_url)


@register.filter
def cropscale(filename, size='200x200'):
    if not (filename and 'x' in size):
        # Better return empty than crash
        return u''

    w, h = [tryint(x) for x in size.split('x')]

    try:
        basename, format = filename.rsplit('.', 1)
    except ValueError:
        basename, format = filename, 'jpg'
    miniature = basename + '_cropscale_' + size + '.' +  format
    miniature_filename = os.path.join(settings.MEDIA_ROOT, miniature).encode('utf-8')
    miniature_url = os.path.join(settings.MEDIA_URL, miniature).encode('utf-8')
    orig_filename = os.path.join(settings.MEDIA_ROOT, filename).encode('utf-8')
    # if the image wasn't already resized, resize it
    if not os.path.exists(miniature_filename) or (os.path.getmtime(miniature_filename)<os.path.getmtime(orig_filename)):
        try:
            image = Image.open(orig_filename)
        except IOError:
            return os.path.join(settings.MEDIA_URL, filename)

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

        try:
            image = image.crop((x_offset, y_offset, x_offset+int(crop_width), y_offset+int(crop_height)))
            image = image.resize((dst_width, dst_height), Image.ANTIALIAS)
            image.save(miniature_filename, image.format, quality=100)
        except IOError:
            return os.path.join(settings.MEDIA_URL, filename)
    return force_unicode(miniature_url)

from __future__ import absolute_import, unicode_literals

from feincms import settings
from feincms.templatetags import feincms_thumbnail
from feincms.utils import get_object


def default_admin_thumbnail(mediafile, dimensions='100x100', **kwargs):
    if mediafile.type != 'image':
        return None

    return feincms_thumbnail.thumbnail(mediafile.file, dimensions)


_cached_thumbnailer = None


def admin_thumbnail(mediafile, dimensions='100x100'):
    global _cached_thumbnailer
    if not _cached_thumbnailer:
        _cached_thumbnailer = get_object(
            settings.FEINCMS_MEDIALIBRARY_THUMBNAIL)
    return _cached_thumbnailer(mediafile, dimensions=dimensions)

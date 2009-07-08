# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from os.path import join

# ------------------------------------------------------------------------
# Settings for MediaLibrary

# Local path to uploaded media files
FEINCMS_MEDIALIBRARY_ROOT = getattr(settings, 'FEINCMS_MEDIALIBRARY_ROOT', settings.MEDIA_ROOT)
# Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_UPLOAD_TO = getattr(settings, 'FEINCMS_MEDIALIBRARY_UPLOAD_TO', 'medialibrary/%Y/%m/')
# URL to access media library files
FEINCMS_MEDIALIBRARY_URL  = getattr(settings, 'FEINCMS_MEDIALIBRARY_URL', settings.MEDIA_URL)

# ------------------------------------------------------------------------
# Settings for RichText

TINYMCE_JS_URL = getattr(settings, 'TINYMCE_JS_URL', join(settings.MEDIA_URL, 'js/tiny_mce/tiny_mce.js'))
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# coding=utf8
# $Id$
# ------------------------------------------------------------------------

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from os.path import join

# ------------------------------------------------------------------------
# Settings for MediaLibrary

# Local path to uploaded media files
FEINCMS_MEDIALIBRARY_PATH = getattr(settings, 'FEINCMS_MEDIALIBRARY_PATH', 'medialibrary/')
# Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_FILES = getattr(settings, 'FEINCMS_MEDIALIBRARY_FILES', FEINCMS_MEDIALIBRARY_PATH + '%Y/%m/')
# URL to access media library files
FEINCMS_MEDIALIBRARY_URL  = getattr(settings, 'FEINCMS_MEDIALIBRARY_URL', '/medialibrary/')

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------

import django
from django.conf import settings
from os.path import join

# Whether Django 1.0 compatibilty mode should be active or not
DJANGO10_COMPAT = django.VERSION[0] < 1 or (django.VERSION[0] == 1 and django.VERSION[1] < 1)

# ------------------------------------------------------------------------
# Settings for MediaLibrary

# Local path to uploaded media files
FEINCMS_MEDIALIBRARY_ROOT = getattr(settings, 'FEINCMS_MEDIALIBRARY_ROOT', settings.MEDIA_ROOT)
# Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_UPLOAD_TO = getattr(settings, 'FEINCMS_MEDIALIBRARY_UPLOAD_TO', 'medialibrary/%Y/%m/')
# URL to access media library files
FEINCMS_MEDIALIBRARY_URL = getattr(settings, 'FEINCMS_MEDIALIBRARY_URL', settings.MEDIA_URL)

# ------------------------------------------------------------------------
# Settings for RichText

TINYMCE_JS_URL = getattr(settings, 'TINYMCE_JS_URL', join(settings.MEDIA_URL, 'js/tiny_mce/tiny_mce.js'))

TINYMCE_CONFIG_URL = getattr(settings, 'TINYMCE_CONFIG_URL', 'admin/content/richtext/init.html')

# ------------------------------------------------------------------------
# Admin settings

FEINCMS_ADMIN_MEDIA = getattr(settings, 'FEINCMS_ADMIN_MEDIA', '/media/sys/feincms/')
# Link to google APIs instead of using local copy of JS libraries
FEINCMS_ADMIN_MEDIA_HOTLINKING = getattr(settings, 'FEINCMS_ADMIN_MEDIA_HOTLINKING', False)

# ------------------------------------------------------------------------
# Settings for the page module

# Use SplitPaneEditor instead of TreeEditor in the page administration
FEINCMS_PAGE_USE_SPLIT_PANE_EDITOR = getattr(settings, 'FEINCMS_PAGE_USE_SPLIT_PANE_EDITOR', False)

FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS = getattr(settings, 'FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS', False)

FEINCMS_ADMIN_TREE_DRAG_AND_DROP = getattr(settings, 'FEINCMS_ADMIN_TREE_DRAG_AND_DROP', True)

# ------------------------------------------------------------------------
# Enable caching intermediate results in feincms. Be aware that this might deliver
# slightly out of date pages if you are not using the 'changedate' page extension.

FEINCMS_USE_CACHE = getattr(settings, 'FEINCMS_USE_CACHE', False)

# ------------------------------------------------------------------------
# Logging class. Defaults to a "do nothing" variant.

FEINCMS_LOGGING_CLASS = getattr(settings, 'FEINCMS_LOGGING_CLASS', 'feincms.logging.LogBase')

# ------------------------------------------------------------------------
# Allow random gunk after a valid (non appcontent) page?

FEINCMS_ALLOW_EXTRA_PATH = getattr(settings, 'FEINCMS_ALLOW_EXTRA_PATH', False)

# ------------------------------------------------------------------------
# How to switch languages.
#   STANDARD = the page a user navigates to sets the site's language and overwrites
#              whatever was set before
#   EXPLICIT = the language set has priority, may only be overridden by explicitely
#              setting a language with ?set_language=xx

FEINCMS_TRANSLATION_POLICY = getattr(settings, 'FEINCMS_TRANSLATION_POLICY', 'STANDARD')

# ------------------------------------------------------------------------

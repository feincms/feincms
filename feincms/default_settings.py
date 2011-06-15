# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------
"""
Default settings for FeinCMS

All of these can be overridden by specifying them in the standard
``settings.py`` file.
"""

from os.path import join

import django
from django.conf import settings

# ------------------------------------------------------------------------
# Settings for MediaLibrary

#: Local path to uploaded media files
FEINCMS_MEDIALIBRARY_ROOT = getattr(settings, 'FEINCMS_MEDIALIBRARY_ROOT', settings.MEDIA_ROOT)
#: Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_UPLOAD_TO = getattr(settings, 'FEINCMS_MEDIALIBRARY_UPLOAD_TO', 'medialibrary/%Y/%m/')
#: URL to access media library files
FEINCMS_MEDIALIBRARY_URL = getattr(settings, 'FEINCMS_MEDIALIBRARY_URL', settings.MEDIA_URL)

# ------------------------------------------------------------------------
# Settings for RichText

FEINCMS_RICHTEXT_INIT_TEMPLATE = getattr(settings, 'FEINCMS_RICHTEXT_INIT_TEMPLATE',
    'admin/content/richtext/init_tinymce.html')
FEINCMS_RICHTEXT_INIT_CONTEXT = getattr(settings, 'FEINCMS_RICHTEXT_INIT_CONTEXT', {
    'TINYMCE_JS_URL': join(settings.MEDIA_URL, 'js/tiny_mce/tiny_mce.js'),
    'TINYMCE_CONTENT_CSS_URL': None,
    'TINYMCE_LINK_LIST_URL': None
    })

# ------------------------------------------------------------------------
# Admin media settings

#: Path to FeinCMS' admin media
FEINCMS_ADMIN_MEDIA = getattr(settings, 'FEINCMS_ADMIN_MEDIA', '/static/feincms/')
#: Link to google APIs instead of using local copy of JS libraries
FEINCMS_ADMIN_MEDIA_HOTLINKING = getattr(settings, 'FEINCMS_ADMIN_MEDIA_HOTLINKING', False)
#: avoid jQuery conflicts -- scripts should use feincms.jQuery instead of $
FEINCMS_JQUERY_NO_CONFLICT = \
    getattr(settings, 'FEINCMS_JQUERY_NO_CONFLICT', False)

# ------------------------------------------------------------------------
# Settings for the page module

#: Include ancestors in filtered tree editor lists
FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS = getattr(settings, 'FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS', False)

#: Show frontend-editing button?
FEINCMS_FRONTEND_EDITING = getattr(settings, 'FEINCMS_FRONTEND_EDITING', True)

#: Enable checking of object level permissions. Note that if this option is enabled,
#: you must plug in an authentication backend that actually does implement object
#: level permissions or no page will be editable.
FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS = getattr(settings, 'FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS', False)

# ------------------------------------------------------------------------
# Various settings

# ------------------------------------------------------------------------
#: Enable caching intermediate results in feincms. Be aware that this might deliver
#: slightly out of date pages if you are not using the 'changedate' page extension.
FEINCMS_USE_CACHE = getattr(settings, 'FEINCMS_USE_CACHE', False)

# ------------------------------------------------------------------------
#: Allow random gunk after a valid page?
FEINCMS_ALLOW_EXTRA_PATH = getattr(settings, 'FEINCMS_ALLOW_EXTRA_PATH', False)

# ------------------------------------------------------------------------
#: How to switch languages.
#:   STANDARD = the page a user navigates to sets the site's language and overwrites
#:              whatever was set before
#:   EXPLICIT = the language set has priority, may only be overridden by explicitely
#:              setting a language with ?set_language=xx
FEINCMS_TRANSLATION_POLICY = getattr(settings, 'FEINCMS_TRANSLATION_POLICY', 'STANDARD')

# ------------------------------------------------------------------------
#: Set to True if you want to run the FeinCMS test suite unconditionally:
FEINCMS_RUN_TESTS = getattr(settings, 'FEINCMS_RUN_TESTS', False)

# ------------------------------------------------------------------------
# Settings for HTML validation

#: If True, HTML will be run through a tidy function before saving:
FEINCMS_TIDY_HTML = getattr(settings, 'FEINCMS_TIDY_HTML', False)
#: If True, displays form validation errors so the user can see how their HTML has been changed:
FEINCMS_TIDY_SHOW_WARNINGS = getattr(settings, 'FEINCMS_TIDY_SHOW_WARNINGS', True)
#: If True, users will be allowed to ignore HTML warnings (errors are always blocked):
FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE = getattr(settings, 'FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE', True)
#: Name of the tidy function - anything which takes (html) and returns (html, errors, warnings) can be used:
FEINCMS_TIDY_FUNCTION = getattr(settings, 'FEINCMS_TIDY_FUNCTION', 'feincms.utils.html.tidy.tidy_html')

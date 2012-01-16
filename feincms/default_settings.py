# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
Default settings for FeinCMS

All of these can be overridden by specifying them in the standard
``settings.py`` file.
"""

from os.path import join

from django.conf import settings

# ------------------------------------------------------------------------
# Settings for MediaLibrary

#: Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_UPLOAD_TO = getattr(settings, 'FEINCMS_MEDIALIBRARY_UPLOAD_TO', 'medialibrary/%Y/%m/')

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

#: avoid jQuery conflicts -- scripts should use feincms.jQuery instead of $
FEINCMS_JQUERY_NO_CONFLICT = \
    getattr(settings, 'FEINCMS_JQUERY_NO_CONFLICT', False)

# Django's admin media files have been transitioned over to standard staticfiles.
# ADMIN_MEDIA_PREFIX isn't available anymore with newer versions (Django >= 1.4).
if hasattr(settings, 'ADMIN_MEDIA_PREFIX'):
    _HACK_ADMIN_MEDIA_IMAGES = settings.ADMIN_MEDIA_PREFIX + 'img/admin/'
else:
    _HACK_ADMIN_MEDIA_IMAGES = settings.STATIC_URL + 'admin/img/'

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
# Settings for HTML validation

#: If True, HTML will be run through a tidy function before saving:
FEINCMS_TIDY_HTML = getattr(settings, 'FEINCMS_TIDY_HTML', False)
#: If True, displays form validation errors so the user can see how their HTML has been changed:
FEINCMS_TIDY_SHOW_WARNINGS = getattr(settings, 'FEINCMS_TIDY_SHOW_WARNINGS', True)
#: If True, users will be allowed to ignore HTML warnings (errors are always blocked):
FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE = getattr(settings, 'FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE', True)
#: Name of the tidy function - anything which takes (html) and returns (html, errors, warnings) can be used:
FEINCMS_TIDY_FUNCTION = getattr(settings, 'FEINCMS_TIDY_FUNCTION', 'feincms.utils.html.tidy.tidy_html')

# ------------------------------------------------------------------------
#: Monkey-patch django.core.urlresvolers.reverse to be application-content aware?
#: (The monkey patch is deprecated and should not be used anymore. Use the
#: ``app_reverse`` function and the ``{% app_reverse %}`` template tag instead.)
#: The value of this setting will be changed to False in FeinCMS 1.6.
FEINCMS_REVERSE_MONKEY_PATCH = getattr(settings, 'FEINCMS_REVERSE_MONKEY_PATCH', True)

# ------------------------------------------------------------------------
#: Makes the page handling mechanism try to find a cms page with that
#: path if it encounters a page not found situation. This allows for nice
#: customised cms-styled error pages. Do not go overboard, this should
#: be as simple and as error resistant as possible, so refrain from
#: deeply nested error pages or advanced content types.
FEINCMS_CMS_404_PAGE = getattr(settings, 'FEINCMS_CMS_404_PAGE', None)

# ------------------------------------------------------------------------
#: When uploading files to the media library, replacing an existing entry,
#: try to save the new file under the old file name in order to keep the
#: media file path (and thus the media url) constant.
#: Experimental, this might not work with all storage backends.
FEINCMS_MEDIAFILE_OVERWRITE = getattr(settings, 'FEINCMS_MEDIAFILE_OVERWRITE', False)

# ------------------------------------------------------------------------

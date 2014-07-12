# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
Default settings for FeinCMS

All of these can be overridden by specifying them in the standard
``settings.py`` file.
"""

from __future__ import absolute_import, unicode_literals

from django.conf import settings

# ------------------------------------------------------------------------
# Settings for Generic Content

# e.g. 'uploads' if you would prefer <media root>/uploads/imagecontent/test.jpg
# to <media root>/imagecontent/test.jpg.
FEINCMS_UPLOAD_PREFIX = getattr(
    settings,
    'FEINCMS_UPLOAD_PREFIX',
    '')

# ------------------------------------------------------------------------
# Settings for MediaLibrary

#: Local path to newly uploaded media files
FEINCMS_MEDIALIBRARY_UPLOAD_TO = getattr(
    settings,
    'FEINCMS_MEDIALIBRARY_UPLOAD_TO',
    'medialibrary/%Y/%m/')

#: Thumbnail function for suitable mediafiles. Only receives the media file
#: and should return a thumbnail URL (or nothing).
FEINCMS_MEDIALIBRARY_THUMBNAIL = getattr(
    settings,
    'FEINCMS_MEDIALIBRARY_THUMBNAIL',
    'feincms.module.medialibrary.thumbnail.default_admin_thumbnail')

# ------------------------------------------------------------------------
# Settings for RichText

FEINCMS_RICHTEXT_INIT_TEMPLATE = getattr(
    settings,
    'FEINCMS_RICHTEXT_INIT_TEMPLATE',
    'admin/content/richtext/init_tinymce4.html')
FEINCMS_RICHTEXT_INIT_CONTEXT = getattr(
    settings,
    'FEINCMS_RICHTEXT_INIT_CONTEXT', {
        'TINYMCE_JS_URL': '//tinymce.cachefly.net/4.1/tinymce.min.js',
        'TINYMCE_DOMAIN': None,
        'TINYMCE_CONTENT_CSS_URL': None,
        'TINYMCE_LINK_LIST_URL': None
    }
)

# ------------------------------------------------------------------------
# Admin media settings

#: avoid jQuery conflicts -- scripts should use feincms.jQuery instead of $
FEINCMS_JQUERY_NO_CONFLICT = getattr(
    settings,
    'FEINCMS_JQUERY_NO_CONFLICT',
    False)

# ------------------------------------------------------------------------
# Settings for the page module

#: Include ancestors in filtered tree editor lists
FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS = getattr(
    settings,
    'FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS',
    False)

#: Show frontend-editing button?
FEINCMS_FRONTEND_EDITING = getattr(
    settings,
    'FEINCMS_FRONTEND_EDITING',
    False)

#: Enable checking of object level permissions. Note that if this option is
#: enabled, you must plug in an authentication backend that actually does
#: implement object level permissions or no page will be editable.
FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS = getattr(
    settings,
    'FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS',
    False)

#: When enabled, the page module is automatically registered with Django's
#: default admin site (this is activated by default).
FEINCMS_USE_PAGE_ADMIN = getattr(
    settings,
    'FEINCMS_USE_PAGE_ADMIN',
    True)

#: app_label.model_name as per django.db.models.get_model.
#: defaults to page.Page
FEINCMS_DEFAULT_PAGE_MODEL = getattr(
    settings,
    'FEINCMS_DEFAULT_PAGE_MODEL',
    'page.Page')

# ------------------------------------------------------------------------
# Various settings

#: Run the weak replacement for a real database migration solution?
FEINCMS_CHECK_DATABASE_SCHEMA = getattr(
    settings,
    'FEINCMS_CHECK_DATABASE_SCHEMA',
    False)

# ------------------------------------------------------------------------
#: Allow random gunk after a valid page?
FEINCMS_ALLOW_EXTRA_PATH = getattr(
    settings,
    'FEINCMS_ALLOW_EXTRA_PATH',
    False)

# ------------------------------------------------------------------------
#: How to switch languages.
#: * ``'STANDARD'``: The page a user navigates to sets the site's language
#:   and overwrites whatever was set before.
#: * ``'EXPLICIT'``: The language set has priority, may only be overridden
#:   by explicitely a language with ``?set_language=xx``.
FEINCMS_TRANSLATION_POLICY = getattr(
    settings,
    'FEINCMS_TRANSLATION_POLICY',
    'STANDARD')

# ------------------------------------------------------------------------
# Settings for HTML validation

#: If True, HTML will be run through a tidy function before saving:
FEINCMS_TIDY_HTML = getattr(
    settings,
    'FEINCMS_TIDY_HTML',
    False)
#: If True, displays form validation errors so the user can see how their
#: HTML has been changed:
FEINCMS_TIDY_SHOW_WARNINGS = getattr(
    settings,
    'FEINCMS_TIDY_SHOW_WARNINGS',
    True)
#: If True, users will be allowed to ignore HTML warnings (errors are always
#: blocked):
FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE = getattr(
    settings,
    'FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE',
    True)
#: Name of the tidy function - anything which takes ``(html)`` and returns
#: ``(html, errors, warnings)`` can be used:
FEINCMS_TIDY_FUNCTION = getattr(
    settings,
    'FEINCMS_TIDY_FUNCTION',
    'feincms.utils.html.tidy.tidy_html')

# ------------------------------------------------------------------------
#: Makes the page handling mechanism try to find a cms page with that
#: path if it encounters a page not found situation. This allows for nice
#: customised cms-styled error pages. Do not go overboard, this should
#: be as simple and as error resistant as possible, so refrain from
#: deeply nested error pages or advanced content types.
FEINCMS_CMS_404_PAGE = getattr(
    settings,
    'FEINCMS_CMS_404_PAGE',
    None)

# ------------------------------------------------------------------------
#: When uploading files to the media library, replacing an existing entry,
#: try to save the new file under the old file name in order to keep the
#: media file path (and thus the media url) constant.
#: Experimental, this might not work with all storage backends.
FEINCMS_MEDIAFILE_OVERWRITE = getattr(
    settings,
    'FEINCMS_MEDIAFILE_OVERWRITE',
    False)

# ------------------------------------------------------------------------
#: Prefix for thumbnails. Set this to something non-empty to separate thumbs
#: from uploads. The value should end with a slash, but this is not enforced.
FEINCMS_THUMBNAIL_DIR = getattr(
    settings,
    'FEINCMS_THUMBNAIL_DIR',
    '_thumbs/')

# ------------------------------------------------------------------------
#: Prevent changing template within admin for pages which have been
#: allocated a Template with singleton=True -- template field will become
#: read-only for singleton pages.
FEINCMS_SINGLETON_TEMPLATE_CHANGE_ALLOWED = getattr(
    settings,
    'FEINCMS_SINGLETON_TEMPLATE_CHANGE_ALLOWED',
    False)

#: Prevent admin page deletion for pages which have been allocated a
#: Template with singleton=True
FEINCMS_SINGLETON_TEMPLATE_DELETION_ALLOWED = getattr(
    settings,
    'FEINCMS_SINGLETON_TEMPLATE_DELETION_ALLOWED',
    False)

# ------------------------------------------------------------------------

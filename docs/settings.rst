.. _settings:

========
Settings
========

FeinCMS has a few installation-wide settings which you might want to customize.

The default settings can be found inside :mod:`feincms.default_settings`.
FeinCMS reads the settings from :mod:`feincms.settings` -- values should be
overridden by placing them in your project's settings.


Content type specific settings
==============================

``FEINCMS_UPLOAD_PREFIX``: Defaults to ``''``. Defines a prefix which is used
for file and image content uploads (not used by the media library).


Media library settings
======================

``FEINCMS_MEDIALIBRARY_UPLOAD_TO``: Defaults to ``medialibrary/%Y/%m``. Defines
the location of newly uploaded media files.

``FEINCMS_MEDIALIBRARY_THUMBNAIL``: Defaults to
``feincms.module.medialibrary.thumbnail.default_admin_thumbnail``. The path to
a function which should return the URL to a thumbnail or ``None`` for the
mediafile instance passed as first argument.

``FEINCMS_MEDIAFILE_OVERWRITE``: Defaults to ``False``. Set this to ``True``
if uploads should replace previous files using the same path if possible. This
allows copy-pasted paths to work, but prevents using far future expiry headers
for media files. Also, it might not work with all storage backends.


Rich text settings
==================

``FEINCMS_RICHTEXT_INIT_TEMPLATE``: Defaults to
``admin/content/richtext/init_tinymce4.html``. The template which contains the
initialization snippet for the rich text editor. Bundled templates are:

* ``admin/content/richtext/init_tinymce.html`` for TinyMCE 3.x.
* ``admin/content/richtext/init_tinymce4.html`` for TinyMCE 4.x.
* ``admin/content/richtext/init_ckeditor.html`` for CKEditor.

``FEINCMS_RICHTEXT_INIT_CONTEXT``: Defaults to
``{'TINYMCE_JS_URL': '<<MEDIA_URL>>js/tiny_mce/tiny_mce.js'}``. A dictionary
which is passed to the template mentioned above. Please refer to the templates
directly to see all available variables.


Admin media settings
====================

``FEINCMS_JQUERY_NO_CONFLICT``: Defaults to ``False``. Django admin's jQuery is
not available as ``$`` or ``jQuery`` in the browser, but only as
``django.jQuery``. FeinCMS' jQuery can be made available only as
``feincms.jQuery`` by setting this variable to ``True``. Scripts should use
``feincms.jQuery`` anyway.


Settings for the tree editor
============================

``FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS``: Defaults to ``False``. When this
setting is ``True``, the tree editor shows all objects on a single page, and
also shows all ancestors up to the roots in filtered lists.


``FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS``: Defaults to ``False``. Enables
checking of object level permissions.


Settings for the page module
============================

``FEINCMS_FRONTEND_EDITING``: Defaults to ``False``. Activate this to show
the frontend editing button in the page change form.

``FEINCMS_USE_PAGE_ADMIN``: Defaults to ``True``. The page model admin module
automatically registers the page model with the default admin site if this is
active. Set to ``False`` if you have to configure the page admin module
yourself.

``FEINCMS_DEFAULT_PAGE_MODEL``: Defaults to ``page.Page``. The page model used
by :mod:`feincms.module.page`.

``FEINCMS_ALLOW_EXTRA_PATH``: Defaults to ``False``. Activate this to allow
random gunk after a valid page URL. The standard behavior is to raise a 404
if extra path elements aren't handled by a content type's ``process()`` method.

``FEINCMS_TRANSLATION_POLICY``: Defaults to ``STANDARD``.  How to switch
languages.

* ``'STANDARD'``: The page a user navigates to sets the site's language
  and overwrites whatever was set before.
* ``'EXPLICIT'``: The language set has priority, may only be overridden
  by explicitely a language with ``?set_language=xx``.

``FEINCMS_FRONTEND_LANGUAGES``: Defaults to None; set it to a list of allowed
language codes in the front end so to allow additional languages in the admin
back end for preparing those pages while not yet making the available to the
public.

``FEINCMS_CMS_404_PAGE``: Defaults to ``None``. Set this if you want the page
handling mechanism to try and find a CMS page with that path if it encounters
a page not found situation.

``FEINCMS_SINGLETON_TEMPLATE_CHANGE_ALLOWED``: Defaults to ``False``.  Prevent
changing template within admin for pages which have been allocated a Template
with ``singleton=True`` -- template field will become read-only for singleton
pages.

``FEINCMS_SINGLETON_TEMPLATE_DELETION_ALLOWED``: Defaults to ``False``.
Prevent admin page deletion for pages which have been allocated a Template with
``singleton=True``.


Settings for HTML validation
============================

These settings are currently only used by the bundled rich text content type.

``FEINCMS_TIDY_HTML``. Defaults to ``False``. If ``True``, HTML will be run
through a tidy function before saving.

``FEINCMS_TIDY_SHOW_WARNINGS``: Defaults to ``True``.  If ``True``, displays
form validation errors so the user can see how their HTML has been changed.

``FEINCMS_TIDY_ALLOW_WARNINGS_OVERRIDE``: Defaults to ``True``.  If ``True``,
users will be allowed to ignore HTML warnings (errors are always blocked).

``FEINCMS_TIDY_FUNCTION``: Defaults to ``feincms.utils.html.tidy.tidy_html``.
Name of the tidy function - anything which takes ``(html)`` and returns
``(html, errors, warnings)`` can be used.


Various settings
================

``FEINCMS_THUMBNAIL_DIR``: Defaults to ``_thumbs/``. Defines a prefix for media
file thumbnails. This allows you to easily remove all thumbnails without fear
of removing files belonging to image and file fields.

``FEINCMS_CHECK_DATABASE_SCHEMA``: Defaults to ``False``. Run the home-grown
schema checker on the page module. Should not be used anymore, use South or
Django 1.7's own migrations support.

.. _settings:

========
Settings
========

FeinCMS has a few installation-wide settings which you might want to customize.

The default settings can be found inside :mod:`feincms.default_settings`.
FeinCMS reads the settings from :mod:`feincms.settings` -- values should be
overridden by placing them in your project's settings.


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
``{'TINYMCE_JS_URL': 'https://cdnjs.cloudflare.com/ajax/libs/tinymce/4.9.11/tinymce.min.js'}``.
A dictionary which is passed to the template mentioned above. Please
refer to the templates directly to see all available variables.


Settings for the tree editor
============================

``FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS``: Defaults to ``False``. When this
setting is ``True``, the tree editor shows all objects on a single page, and
also shows all ancestors up to the roots in filtered lists.


``FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS``: Defaults to ``False``. Enables
checking of object level permissions.


Settings for the page module
============================

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

``FEINCMS_MEDIAFILE_TRANSLATIONS``: Defaults to ``True``. Set to ``False`` if
you want FeinCMS to not translate ``MediaFile`` names, and instead just use the
filename directly.


Various settings
================

``FEINCMS_THUMBNAIL_DIR``: Defaults to ``_thumbs/``. Defines a prefix for media
file thumbnails. This allows you to easily remove all thumbnails without fear
of removing files belonging to image and file fields.

``FEINCMS_THUMBNAIL_CACHE_TIMEOUT``: ``feincms_thumbnail`` template
filter library cache timeout. The default is to not cache anything for
backwards compatibility. If you use cloud storage AND
``feincms_thumbnail`` it is recommended to set the timeout to a large
value.

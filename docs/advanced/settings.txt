.. _advanced-settings:

Settings
========

.. module:: feincms.settings


You can set values for all these settings inside your ``settings.py`` file.
The :mod:`feincms.settings` module tries to provide sane default values for
most of these, but not for all.


* ``FEINCMS_ADMIN_MEDIA``:

  Path to the FeinCMS admin Javascript, CSS and image files. Comparable to
  ``ADMIN_MEDIA_PREFIX`` from Django proper.

  Defaults to ``/media/sys/feincms/``

* ``FEINCMS_ADMIN_MEDIA_HOTLINKING``:

  Hotlink jQuery and jQuery-UI files from the Google servers. Has the potential
  to make the admin page load faster because files can be loaded from several
  servers at the same time, but is not always available. Furthermore, all of
  jQuery-UI is included if you use this, but only a small subset is actually
  used at the current time.

  Defaults to ``False``

* ``TINYMCE_JS_URL``:

  The complete path to the main TinyMCE Javascript file. Only required if you
  use the :class:`~feincms.content.richtext.models.RichTextContent`.

  Defaults to ``settings.MEDIA_URL + 'js/tiny_mce/tiny_mce.js'``

* ``FEINCMS_MEDIALIBRARY_ROOT``:

  Where the media library should store its media files.

  Defaults to ``settings.MEDIA_ROOT``

* ``FEINCMS_MEDIALIBRARY_UPLOAD_TO``:

  ``upload_to`` argument for the media file :class:`FileField`.

  Defaults to ``medialibrary/%Y/%m/``

* ``FEINCMS_MEDIALIBRARY_URL``:

  URL where media files can be accessed.

  Defaults to ``settings.MEDIA_URL``


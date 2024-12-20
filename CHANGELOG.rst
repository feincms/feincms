.. _changelog:

Change log
==========

Next version
~~~~~~~~~~~~

- Added a tinymce 7 integration for the richtext content type.


v24.8.1 (2024-08-07)
~~~~~~~~~~~~~~~~~~~~

- Fixed another edge case: JPEGs cannot be saved as RGBA.
- Added Django 5.1 to the CI.


v24.7.1 (2024-07-10)
~~~~~~~~~~~~~~~~~~~~

- Fixed the read the docs build.
- Disabled the CKEditor 4 version nag.


v24.4.2 (2024-04-18)
~~~~~~~~~~~~~~~~~~~~

- Fixed the filters to work with Django 5.


v24.4.1 (2024-04-16)
~~~~~~~~~~~~~~~~~~~~

- Forwarded cookies set by ``ApplicationContent`` apps to the final response.
- Added support for webp image formats to the media library.


v24.4.0 (2024-04-08)
~~~~~~~~~~~~~~~~~~~~

- Fetched the CSRF token value from the input field instead of from the cookie.
  This allows making the CSRF cookie ``httponly``. Thanks to Samuel Lim for the
  contribution!


v23.12.0 (2023-12-22)
~~~~~~~~~~~~~~~~~~~~~

- Added Python 3.12, Django 5.0.
- Closed images after reading their dimensions. Raised the logging level to
  exception when thumbnailing fails. Thanks to Jeroen Pulles for those two
  contributions!


`v23.8.0`_ (2023-08-07)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v23.8.0: https://github.com/feincms/feincms/compare/v23.1.0...v23.8.0

- Made the filter argument of content base's ``get_queryset`` method optional.
  This enables easier interoperability of FeinCMS content types with feincms3
  plugins.
- Added Python 3.11.
- Fixed the Pillow resampling constant.


`v23.1.0`_ (2023-03-09)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v23.1.0: https://github.com/feincms/feincms/compare/v22.4.0...v23.1.0

- Fixed a place where ``ACTION_CHECKBOX_NAME`` was imported from the wrong
  place.
- Dropped the ``is_dst`` argument to ``timezone.make_aware``.
- Added Django 4.1 and 4.2 to the CI matrix.


`v22.4.0`_ (2022-06-02)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v22.4.0: https://github.com/feincms/feincms/compare/v22.3.0...v22.4.0

- Changed the ``template_key`` field type to avoid boring migrations because of
  changing choices.


`v22.3.0`_ (2022-05-17)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v22.3.0: https://github.com/feincms/feincms/compare/v22.2.0...v22.3.0

- The ``render()`` methods of bundled content types have been changed to return
  a tuple instead of a HTML fragment in FeinCMS v22.0.0. This was backwards
  incompatible in some scenarios. Those methods have been changed to return a
  tuple subclass which automatically renders a HTML fragment if evaluated in a
  string context.


`v22.2.0`_ (2022-05-06)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v22.2.0: https://github.com/feincms/feincms/compare/v22.1.0...v22.2.0

- Dropped support for Python < 3.8.
- Fixed the thumbnailing support of the ``MediaFileForeignKey``. It has been
  broken since Django switched to template-based widget rendering.


`v22.1.0`_ (2022-03-31)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v22.1.0: https://github.com/feincms/feincms/compare/v22.0.0...v22.1.0

- Fixed the ``feincms_render_level`` render recursion protection.
- Wrapped the recursive saving of pages in a transaction, so if anything fails
  we have a consistent state.
- Dropped more compatibility code for Django 1.x.
- Made ``medialibrary_orphans`` work again.
- Removed the ``six`` dependency since we're Python 3-only now.
- Updated the pre-commit hooks, cleaned up the JavaScript a bit.


`v22.0.0`_ (2022-01-07)
~~~~~~~~~~~~~~~~~~~~~~~

.. _v22.0.0: https://github.com/feincms/feincms/compare/v1.20.0...v22.0.0

- **Possibly backwards incompatible** Changed all bundled content types'
  ``render()`` methods to return the ``(template_name, context)`` tuple instead
  of rendering content themselves.
- Dropped compatibility guarantees with Python < 3.6, Django < 3.2.
- Added pre-commit.
- The default view was changed to accept the path as a ``path`` keyword
  argument, not only as a positional argument.
- Changed the item editor action buttons CSS to not use transitions so that the
  sprite buttons look as they should.


`v1.20.0`_ (2021-03-22)
~~~~~~~~~~~~~~~~~~~~~~~

- Changed ``#main`` to the more specific ``#feincmsmain`` so that it doesn't
  collide with Django's admin panel markup.
- Stopped the JavaScript code from constructing invalid POST action URLs in the
  change form.
- Renamed the main branch to main.
- Switched to a declarative setup.
- Switched to GitHub actions.
- Sorted imports.
- Reformated the JavaScript code using prettier.
- Added Python up to 3.9, Django up to the main branch (the upcoming 4.0) to
  the CI list.


`v1.19.0`_ (2021-03-04)
~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a bug where the thumbnailer would try to save JPEGs as RGBA.
- Reformatted the code using black, again.
- Added Python 3.8, Django 3.1 to the build.
- Added the Django 3.2 `.headers` property to the internal dummy response used
  in the etag request processor.
- Added a workaround for ``AppConfig``-autodiscovery related crashes. (Because
  ``feincms.apps`` now has more meanings). Changed the documentation to prefer
  ``feincms.content.application.models.*`` to ``feincms.apps.*``.
- Updated the TinyMCE CDN URL to an version which doesn't show JavaScript
  alerts.
- Added missing ``on_delete`` values to the django-filer content types.


`v1.18.0`_ (2020-01-21)
~~~~~~~~~~~~~~~~~~~~~~~

- Added a style checking job to the CI matrix.
- Dropped compatibility with Django 1.7.


`v1.17.0`_ (2019-11-21)
~~~~~~~~~~~~~~~~~~~~~~~

- Added compatibility with Django 3.0.


`v1.16.0`_ (2019-02-01)
~~~~~~~~~~~~~~~~~~~~~~~

- Reformatted everything using black.
- Added a fallback import for the ``staticfiles`` template tag library
  which will be gone in Django 3.0.


`v1.15.0`_ (2018-12-21)
~~~~~~~~~~~~~~~~~~~~~~~

- Actually made use of the timeout specified as
  ``FEINCMS_THUMBNAIL_CACHE_TIMEOUT`` instead of the hardcoded value of
  seven days.
- Reverted the deprecation of navigation extension autodiscovery.
- Fixed the item editor JavaScript and HTML to work with Django 2.1's
  updated inlines.
- Fixed ``TranslatedObjectManager.only_language`` to evaluate callables
  before filtering.
- Changed the ``render`` protocol of content types to allow returning a
  tuple of ``(ct_template, ct_context)`` which works the same way as
  `feincms3's template renderers
  <https://feincms3.readthedocs.io/en/latest/guides/rendering.html>`__.


`v1.14.0`_ (2018-08-16)
~~~~~~~~~~~~~~~~~~~~~~~

- Added a central changelog instead of creating release notes per
  release because development is moving more slowly owing to the stable
  nature of FeinCMS.
- Fixed history (revision) form, recover form and breadcrumbs when
  FeinCMS is used with Reversion 2.0.x. This accommodates refactoring
  that took place in `Reversion 1.9 and 2.0
  <https://django-reversion.readthedocs.io/en/stable/changelog.html>`_.
  If you are upgrading Reversion (rather than starting a new project),
  please be aware of the significant interface changes and database
  migrations in that product, and attempt upgrading in a development
  environment before upgrading a live site.
- Added ``install_requires`` back to ``setup.py`` so that dependencies
  are installed automatically again. Note that some combinations of e.g.
  Django and django-mptt are incompatible -- look at the `Travis CI
  build configuration
  <https://github.com/feincms/feincms/blob/master/.travis.yml>`_ to find
  out about supported combinations.
- Fixed a few minor compatibility and performance problems.
- Added a new ``FEINCMS_THUMBNAIL_CACHE_TIMEOUT`` setting which allows
  caching whether a thumb exists instead of calling ``storage.exists()``
  over and over (which might be slow with remote storages).
- Fixed random reordering of applications by using an ordered dictionary
  for apps.
- Increased the length of the caption field for media file translations.
- Fixed ``feincms.contrib.tagging`` to actually work with Django
  versions after 1.9.x.


.. _v1.14.0: https://github.com/feincms/feincms/compare/v1.13.0...v1.14.0
.. _v1.15.0: https://github.com/feincms/feincms/compare/v1.14.0...v1.15.0
.. _v1.16.0: https://github.com/feincms/feincms/compare/v1.15.0...v1.16.0
.. _v1.17.0: https://github.com/feincms/feincms/compare/v1.16.0...v1.17.0
.. _v1.18.0: https://github.com/feincms/feincms/compare/v1.17.0...v1.18.0
.. _v1.19.0: https://github.com/feincms/feincms/compare/v1.18.0...v1.19.0
.. _v1.20.0: https://github.com/feincms/feincms/compare/v1.19.0...v1.20.0

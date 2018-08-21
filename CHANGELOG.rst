.. _changelog:

Change log
==========

`Next version`_
~~~~~~~~~~~~~~~

- Actually made use of the timeout specified as
  ``FEINCMS_THUMBNAIL_CACHE_TIMEOUT`` instead of the hardcoded value of
  seven days.
- Reverted the deprecation of navigation extension autodiscovery.


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
.. _Next version: https://github.com/feincms/feincms/compare/v1.14.0...master

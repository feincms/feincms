.. _changelog:

Change log
==========

`Next version`_
~~~~~~~~~~~~~~~

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
  are installed automatically again.


.. _Next version: https://github.com/feincms/feincms/compare/v1.13.0...master

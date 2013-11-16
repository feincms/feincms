.. _deprecation:

============================
FeinCMS Deprecation Timeline
============================


This document outlines when various pieces of FeinCMS will be removed or
altered in backward incompatible way. Before a feature is removed, a warning
will be issued for at least two releases.


1.6
===

* The value of ``FEINCMS_REVERSE_MONKEY_PATCH`` has been changed to ``False``.
* Deprecated page manager methods have been removed (``page_for_path_or_404``,
  ``for_request_or_404``, ``best_match_for_request``, ``from_request``) -
  ``Page.objects.for_request()``, ``Page.objects.page_for_path`` and
  ``Page.objects.best_match_for_path`` should cover all use cases.
* Deprecated page methods have been removed (``active_children``,
  ``active_children_in_navigation``, ``get_siblings_and_self``)
* Request and response processors have to be imported from
  :mod:`feincms.module.page.processors`. Additionally, they must be registered
  individually by using ``register_request_processor`` and
  ``register_response_processor``.
* Prefilled attributes have been removed. Use Django's ``prefetch_related``
  or ``feincms.utils.queryset_transform`` instead.
* ``feincms.views.base`` has been moved to ``feincms.views.legacy``. Use
  ``feincms.views.cbv`` instead.
* ``FEINCMS_FRONTEND_EDITING``'s default has been changed to ``False``.
* The code in :mod:`feincms.module.page.models` has been split up. The admin
  classes are in :mod:`feincms.module.page.modeladmin`, the forms in
  :mod:`feincms.module.page.forms` now. Analogous changes have been made
  to :mod:`feincms.module.medialibrary.models`.


1.7
===

* The monkeypatch to make Django's :func:`django.core.urlresolvers.reverse`
  applicationcontent-aware will be removed. Use
  :func:`feincms.content.application.models.app_reverse` and the corresponding
  template tag instead.

* The module :mod:`feincms.content.medialibrary.models` will be replaced by
  the contents of :mod:`feincms.content.medialibrary.v2`. The latter uses
  Django's ``raw_id_fields`` support instead of reimplementing it badly.

* The legacy views inside :mod:`feincms.views.legacy` will be removed.


1.8
===

* The module ``feincms.admin.editor`` will be removed. The model admin classes
  have been available in :mod:`feincms.admin.item_editor` and
  :mod:`feincms.admin.tree_editor` since FeinCMS v1.0.

* Cleansing the HTML of a rich text content will still be possible, but the
  cleansing module :mod:`feincms.utils.html.cleanse` will be removed. When
  creating a rich text content, the ``cleanse`` argument must be a callable
  and cannot be ``True`` anymore. The cleansing function has been moved into
  its own package,
  `feincms-cleanse <http://pypi.python.org/pypi/feincms-cleanse>`_.

* Registering extensions using shorthand notation will be not be possible in
  FeinCMS v1.8 anymore. Use the following method instead::

      Page.register_extensions(
          'feincms.module.page.extensions.navigation',
          'feincms.module.extensions.ct_tracker',
          )

* ``feincms_navigation`` and ``feincms_navigation_extended`` will be removed.
  Their functionality is provided by ``feincms_nav`` instead.

* The function-based generic views aren't available in Django after v1.4
  anymore. :mod:`feincms.views.generic` and
  :func:`feincms.views.decorators.add_page_to_extra_context` will be removed
  as well.

* The module :mod:`feincms.content.medialibrary.v2`, which is only an alias for
  :mod:`feincms.content.medialibrary.models` starting with FeinCMS v1.7 will be
  removed.

* ``Page.setup_request()`` does not do anything anymore and will be removed.


1.9
===

* Fields added through page extensions which haven't been explicitly added
  to the page model admin using ``modeladmin.add_extension_options`` will
  disappear from the admin interface. The automatic collection of fields
  will be removed.

* All extensions should inherit from ``feincms.extensions.Extension``.
  Support for ``register(cls, admin_cls)``-style functions will be removed
  in FeinCMS v1.9.

* The ``_feincms_extensions`` attribute on the page model and on models
  inheriting ``ExtensionsMixin`` is gone.

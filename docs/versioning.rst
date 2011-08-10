.. _versioning:

=====================================================
Versioning database content with ``django-reversion``
=====================================================

The following steps should be followed to integrate the page module
with django-reversion_:

.. _django-reversion: https://github.com/etianen/django-reversion


* Add ``'reversion'`` to the list of installed applications.
* Add ``'reversion.middleware.RevisionMiddleware'`` to ``MIDDLEWARE_CLASSES``.
* Call ``Page.register_with_reversion()`` after all content types have been
  created (after all ``create_content_type`` invocations).

Now, you need to create your own model admin subclass inheriting from both
FeinCMS' ``PageAdmin`` and from reversions ``VersionAdmin``::

    from django.contrib import admin
    from feincms.module.page.models import Page, PageAdmin
    from reversion.admin import VersionAdmin

    admin.site.unregister(Page)

    class VersionedPageAdmin(PageAdmin, VersionAdmin):
        pass

    admin.site.register(Page, VersionedPageAdmin)

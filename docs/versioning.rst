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
* Add ``FEINCMS_USE_PAGE_ADMIN = False`` to your ``settings`` file.

Now, you need to create your own model admin subclass inheriting from both
FeinCMS' ``PageAdmin`` and from reversions ``VersionAdmin``::

    from django.contrib import admin
    from feincms.module.page.models import Page
    from feincms.module.page.modeladmins import PageAdmin
    from reversion.admin import VersionAdmin

    class VersionedPageAdmin(PageAdmin, VersionAdmin):
        pass

    admin.site.register(Page, VersionedPageAdmin)

The ``VersionedPageAdmin`` does not look like the ItemEditor -- it's
just raw Django inlines, without any additional JavaScript. Patches are
welcome, but the basic functionality needed for versioning page content
is there.

Finally, you should ensure that initial revisions are created using
``django-reversion``'s ``createinitialrevisions`` management command.


.. note::

   You should ensure that you're using a reversion release which is
   compatible with your installed Django version. The reversion documentation
   contains an up-to-date list of compatible releases.

   The reversion support in FeinCMS requires at least django-reversion 1.6.

.. note::

   Only the Page module is versioned. MediaFiles are not. If a user deletes an
   image from the MediaLibrary by accident it cannot be recovered.
   Furthermore, if the position of a page has been moved within the tree,
   the recovery will break the tree structure.
   You can try to fix it using the ``rebuild_mptt`` command.

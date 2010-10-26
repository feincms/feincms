.. _admin:

=============================
CMS administration interfaces
=============================

FeinCMS provides two ModelAdmin classes, :class:`~feincms.admin.item_editor.ItemEditor`,
and :class:`~feincms.admin.tree_editor.TreeEditor`. Their purpose and
their customization hooks are briefly discussed here.


The tree editor
===============

.. module:: feincms.admin.tree_editor
.. class:: TreeEditor

The tree editor replaces the standard change list interface with a collapsible
item tree. The model must be registered with `django-mptt <http://github.com/matthiask/django-mptt/>`_
for this to work.

.. image:: images/tree_editor.png

Usage is as follows::

    from django.db import models

    class YourModel(models.Model):
        # model field definitions

        class Meta:
            ordering = ['tree_id', 'lft'] # The TreeEditor needs this ordering definition


And inside your ``admin.py`` file::

    from django.contrib import admin
    from feincms.admin import editor
    from yourapp.models import YourModel

    class YourModelAdmin(editor.TreeEditor):
        pass

    admin.site.register(YourModel, YourModelAdmin)


All standard :class:`~django.contrib.admin.options.ModelAdmin` attributes such as
:attr:`ModelAdmin.list_display`, :attr:`ModelAdmin.list_editable`,
:attr:`ModelAdmin.list_filter` work as normally. The only exception to this
rule is the column showing the tree structure (the second column in the image).
There, we always show the value of :attr:`Model.__unicode__` currently.


AJAX checkboxes
---------------

The tree editor allows you to define boolean columns which let the website
administrator change the value of the boolean using a simple click on the icon.
These boolean columns can be aware of the tree structure. For example, if an object's
``active`` flag influences the state of its descendants, the tree editor interface
is able to show not only the state of the modified element, but also the state of
all its descendants without having to reload the page.

Currently, documentation for this feature is not available yet. You can take a
look at the implementation of the ``is_visible`` and ``in_navigation`` columns of
the page editor however.

Usage::

    from django.contrib import admin
    from feincms.admin import editor
    import mptt

    class Category(models.Model):
        active = models.BooleanField()
        name = models.CharField(...)
        parent = models.ForeignKey('self', blank=True, null=True)

        # ...
    mptt.register(Category)

    class CategoryAdmin(editor.TreeEditor):
        list_display = ('__unicode__', 'active_toggle')
        active_toggle = editor.ajax_editable_boolean('active', _('active'))



The item editor
===============

.. module:: feincms.admin.item_editor
.. class:: ItemEditor

The tabbed interface below is used to edit content and other properties of the
edited object. A tab is shown for every region of the template or element,
depending on whether templates are activated for the object in question [#f1]_.

Here's an screenshot of a content editing pane. The media file content is
collapsed currently. New items can be added using the control bar at the bottom,
and all content blocks can be reordered using drag and drop:

.. image:: images/item_editor_content.png

.. [#f1] Templates are required for the page module; blog entries managed through
         the item editor probably won't have a use for them.


Customizing the item editor
---------------------------

.. versionadded:: 1.1.5
* The :class:`~feincms.admin.item_editor.ItemEditor` now plays nicely with
  standard Django ``fieldsets``; the content-editor is rendered as a
  replacement for a fieldset with the placeholder name matching
  :const:`~feincms.admin.item_editor.FEINCMS_CONTENT_FIELDSET_NAME`. If no
  such fieldset is present, one is inserted at the top automatically. If you
  wish to customise the location of the content-editor, simple include this
  fieldset at the desired location::

    from feincms.admin.item_editor import ItemEditor, FEINCMS_CONTENT_FIELDSET

    class MyAdmin(ItemEditor):
        fieldsets = (
            ('Important things', {'fields': ('title', 'slug', 'etc')}),
            FEINCMS_CONTENT_FIELDSET,
            ('Less important things',
                {
                    'fields': ('copyright', 'soforth'),
                    'classes': ('collapse',)
                }
            )
        )

.. versionchanged:: 1.1.5
* ``show_on_top`` (**deprecated**; use standard ``fieldsets`` instead)

  A tuple which describes, which fields should be shown above the tabbed item
  editor interface. For backwards compatibility this tuple is converted to
  a fieldset which is prepended to ``fieldsets`` to appear at the top.


Customizing the individual content type forms
---------------------------------------------

Customizing the individual content type editors is easily possible through two
settings on the content type model itself:

* ``feincms_item_editor_context_processors``:

  A list of callables using which you may add additional values to the item
  editor templates.

* ``feincms_item_editor_form``:

  You can specify the base class which should be used for the content type
  model. The default value is :class:`django.forms.ModelForm`.

* ``feincms_item_editor_includes``:

  If you need additional Javascript or CSS files or need to perform additional
  initialization on your content type forms, you can specify template fragments
  which are included in predefined places into the item editor.

  If you need to execute additional Javascript, for example to add a TinyMCE instance,
  it is recommended to add the initialization functions to the
  ``contentblock_init_handlers`` array, because the initialization needs to be
  performed not only on page load, but also after drag-dropping a content block
  and after adding new content blocks. Take a look at the ``mediafile`` and
  ``richtext`` item editor include files to understand how this should be done.



Putting it all together
=======================

Best advice here is taking a look at the files inside :mod:`feincms/module/page/`.

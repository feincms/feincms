.. _index:

========================================
FeinCMS - An extensible Django-based CMS
========================================


.. image:: images/tree_editor.png

FeinCMS is an extremely stupid content management system. It knows
nothing about content -- just enough to create an admin interface for
your own page content types. It lets you reorder page content blocks
using a drag-drop interface, and you can add as many content blocks
to a region (f.e. the sidebar, the main content region or something
else which I haven't thought of yet). It provides helper functions,
which provide ordered lists of page content blocks. That's all.

Adding your own content types is extremely easy. Do you like markdown
that much, that you'd rather die than using a rich text editor?
Then add the following code to your project, and you can go on using the
CMS without being forced to use whatever the developers deemed best::

    from markdown2 import markdown
    from feincms.module.page.models import Page
    from django.db import models

    class MarkdownPageContent(models.Model):
        content = models.TextField()

        class Meta:
            abstract = True

        def render(self, **kwargs):
            return markdown(self.content)

    Page.create_content_type(MarkdownPageContent)


That's it. Only ten lines of code for your own page content type.



Contents
========

.. toctree::
   :maxdepth: 3

   installation
   page
   contenttypes
   extensions
   admin
   integration
   medialibrary
   templatetags
   settings
   migrations
   versioning
   advanced/index
   faq
   contributing
   deprecation


Releases
========

.. toctree::
   :maxdepth: 1

   releases/1.2
   releases/1.3
   releases/1.4
   releases/1.5
   releases/1.6
   releases/1.7
   releases/1.8
   releases/1.9
   releases/1.10
   releases/1.11
   releases/1.12
   releases/1.13


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

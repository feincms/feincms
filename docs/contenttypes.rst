.. _contenttypes:

==========================
Working with content types
==========================

You will learn how to add your own content types and how you can
render them in a template.


What is a content type anyway?
==============================

In FeinCMS, a content type is something to attach as content to a base model,
for example a CMS Page (the base model) may have several rich text components
associated to it (those would be RichTextContent content types).

Every content type knows, amongst other things, how to render itself.
Think of content types as "snippets" of information to appear on a page.


Rendering contents in your templates
====================================

Simple:

::

    <div id="content">
        {% block content %}
        {% for content in feincms_page.content.main %}
            {{ content.render }}
        {% endfor %}
        {% endblock %}
    </div>

    <div id="sidebar">
        {% block sidebar %}
        {% for content in feincms_page.content.sidebar %}
            {{ content.render }}
        {% endfor %}
        {% endblock %}
    </div>


Implementing your own content types
===================================

FeinCMS offers a method on :class:`feincms.models.Base` called
:func:`create_content_type` which will create concrete content types from
your abstract content types. Since content types can be used for different
CMS base models such as pages and blog entries (implementing a rich text
or an image content once and using it for both models makes lots of sense)
your implementation needs to be abstract. :func:`create_content_type` adds
a few utility methods and a few model fields to build the concrete type,
a foreign key to the base model (f.e. the :class:`Page`) and
several properties indicating where the content block will be positioned
in the rendered result.


.. note::
   The examples on this page assume that you use the
   :class:`~feincms.module.page.models.Page` CMS base model. The principles
   outlined apply for all other CMS base types.


Implementing a textile content block
------------------------------------

Without further ado, here's the first example:

::

    from feincms.module.page.models import Page
    from django.contrib.markup.templatetags.markup import textile
    from django.db import models

    class TextilePageContent(models.Model):
        content = models.TextField()

        class Meta:
            abstract = True

        def render(self, **kwargs):
            return textile(self.content)

    Page.create_content_type(TextilePageContent)


There are three field names you should not use because they are added
by ``create_content_type``: These are ``parent``, ``region`` and ``ordering``.
These fields are used to specify the place where the content will be
placed in the output.



Customizing the render method for different regions
===================================================

The default ``render`` method uses the region key to find a render method
in your concrete content type and calls it. This allows you to customize
the output depending on the region; you might want to show the same
content differently in a sidebar and in the main region for example.
If no matching method has been found a ``NotImplementedError`` is raised.

This ``render`` method tries to be a sane default, nothing more. You can
simply override it and put your own code there if you do not any
differentiation, or if you want to do it differently.

All ``render`` methods should accept ``**kwargs``. Some render methods might
need the request, for example to determine the correct Google Maps API
key depending on the current domain without resorting to ugly hacks.

The example above could be rewritten like this:

::

   {% load feincms_tags %}

    <div id="content">
        {% block content %}
        {% for content in feincms_page.content.main %}
            {% feincms_render_content content request %}
        {% endfor %}
        {% endblock %}
    </div>

    <div id="sidebar">
        {% block sidebar %}
        {% for content in feincms_page.content.sidebar %}
            {% feincms_render_content content request %}
        {% endfor %}
        {% endblock %}
    </div>


Or even like this:

::

   {% load feincms_tags %}

    <div id="content">
        {% block content %}
        {% feincms_render_region feincms_page "main" request %}
        {% endblock %}
    </div>

    <div id="sidebar">
        {% block sidebar %}
        {% feincms_render_region feincms_page "sidebar" request %}
        {% endblock %}
    </div>


This does exactly the same, but you do not have to loop over the page content
blocks yourself. You need to add the request context processor to your list
of context processors for this example to work.



Bundled content types
=====================

Application content
-------------------
.. module:: feincms.content.application.models
.. class:: ApplicationContent()

Used to let the administrator freely integrate 3rd party applications into
the CMS. Described in :ref:`integration-applicationcontent`.


Contact form
------------
.. module:: feincms.content.contactform.models
.. class:: ContactForm()

Simple contact form. Also serves as an example how forms might be used inside
content types.


Inline files and images
-----------------------
.. module:: feincms.content.file.models
.. class:: FileContent()
.. module:: feincms.content.image.models
.. class:: ImageContent()

These are simple content types holding just a file or an image with a
position. You should probably use the MediaFileContent though.


Media library integration
-------------------------
.. module:: feincms.content.medialibrary.models
.. class:: MediaFileContent()

Mini-framework for arbitrary file types with customizable rendering
methods per-filetype.  Add 'feincms.module.medialibrary' to INSTALLED_APPS.

Additional arguments for :func:`~feincms.models.Base.create_content_type`:

* ``POSITION_CHOICES``: (mandatory)

  A list of tuples for the position dropdown.


Raw content
-----------
.. module:: feincms.content.raw.models
.. class:: RawContent()

Raw HTML code, f.e. for flash movies or javascript code.


Rich text
---------
.. module:: feincms.content.richtext.models
.. class:: RichTextContent()

TinyMCE widget, stripped down to the essentials; no media support, only
a few styles activated. The TinyMCE javascript files are not included,
you need to put them in the right place on your own.

Please note that you should set the TINYMCE_JS_URL inside your settings,
otherwise settings.MEDIA_URL + 'js/tiny_mce/tiny_mce.js' will be used.

If you pass cleanse=True to the create_content_type invocation for your
RichTextContent types, the HTML code will be cleansed right before saving
to the database everytime the content is modified.

Additional arguments for :func:`~feincms.models.Base.create_content_type`:

* ``cleanse``:

  Whether the HTML code should be cleansed of all tags and attributes
  which are not explicitly whitelisted. The default is ``False``.


RSS feeds
---------
.. module:: feincms.content.rss.models
.. class:: RSSContent

A feed reader widget. This also serves as an example how to build a content
type that needs additional processing, in this case from a cron job. If an
RSS feed has been added to the CMS, ``manage.py update_rsscontent`` should
be run periodically (either through a cron job or through other means) to
keep the shown content up to date.  The `feedparser` module is required.


Video inclusion code for youtube, vimeo etc.
--------------------------------------------
.. module:: feincms.content.video.models
.. class:: VideoContent

A easy-to-use content type that automatically generates Flash video inclusion code
from a website link. Currently only YouTube and Vimeo links are supported.



Restricting a content type to a subset of regions
=================================================

Imagine that you have developed a content type which really only makes sense in
the sidebar, not in the main content area. It is very simple to restrict a
content type to a subset of regions, the only thing you have to do is pass a
tuple of region keys to the create_content_type method:

::

    Page.create_content_type(SomeSidebarContent, regions=('sidebar',))


Note that the restriction only influences the content types shown in the
"Add new item"-dropdown in the item editor. The user may still choose to add
the SomeSidebarContent to the sidebar, for example, and then proceed to move the
content item into the main region.



Design considerations for content types
=======================================

Because the admin interface is already filled with information, it is sometimes
easier to keep the details for certain models outside the CMS content types.
Complicated models do not need to be edited directly in the CMS item editor,
you can instead use the standard Django administration interface for them, and
integrate them into FeinCMS by utilizing foreign keys. Already the bundled
FileContent and ImageContent models can be viewed as bad style in this respect,
because if you want to use a image or file more than once you need to upload it
for every single use instead of being able to reuse the uploaded file. The
media library module and MediaFileContent resolve at least this issue nicely by
allowing the website administrator to attach metadata to a file and
include it in a page by simply selecting the previously uploaded media file.



Configuring and self-checking content types at creation time
============================================================

So you'd like to check whether Django is properly configured for your content
type, or maybe add model/form fields depending on arguments passed at content
type creation time? This is very easy to achieve. The only thing you need to
do is adding a classmethod named :func:`initialize_type` to your content type, and
pass additional keyword arguments to :func:`create_content_type`.

If you want to see an example of these two uses, have a look at the
:class:`~feincms.content.medialibrary.models.MediaFileContent`.

It is generally recommended to use this hook to configure content types
compared to putting the configuration into the site-wide settings file. This
is because you might want to configure the content type differently
depending on the CMS base model that it is used with.


Obtaining a concrete content type model
=======================================

The concrete content type models are stored in the same module as the CMS base
class, but they do not have a name using which you could import them. Accessing
internal attributes is hacky, so what is the best way to get a hold onto the
concrete content type?

There are two recommended ways. The example use a ``RawContent`` content type and
the Page CMS base class.

You could take advantage of the fact that ``create_content_type`` returns the
created model:

::

    from feincms.module.page.models import Page
    from feincms.content.raw.models import RawContent

    PageRawContent = Page.create_content_type(RawContent)


Or you could use :func:`content_type_for`:

::

    from feincms.content.raw.models import RawContent

    PageRawContent = Page.content_type_for(RawContent)

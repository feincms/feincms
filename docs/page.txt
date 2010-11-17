.. _page:

==============================
Using the built-in page module
==============================

.. module:: feincms.module.page

FeinCMS is primarily a system to work with lists of content blocks which
you can assign to arbitrary other objects. You do not necessarily have to
use it with a hierarchical page structure, but that's the most common use
case of course. Being able to put content together in small manageable
pieces is interesting for other uses too, i.e. for weblog entries where you
have rich text content interspersed with images, videos or maybe even galleries.


Activating the page module and creating content types
=====================================================

To activate the page module, you need to follow the instructions in
:ref:`installation` and afterwards add :mod:`feincms.module.page` to your
:data:`INSTALLED_APPS`.

Before proceeding with ``manage.py syncdb``, it might be a good idea to take
a look at :ref:`page-extensions` -- the page module does have the minimum of
features in the default configuration and you will probably want to enable
several extensions.

You need to create some content models too. No models are created by default,
because there is no possibility to unregister models. A sane default might
be to create :class:`~feincms.content.image.models.ImageContent` and
:class:`~feincms.content.richtext.models.RichTextContent` models; you can do this
by adding the following lines somewhere into your project, for example in a
``models.py`` file that will be processed anyway:

::

    from django.utils.translation import ugettext_lazy as _

    from feincms.module.page.models import Page
    from feincms.content.richtext.models import RichTextContent
    from feincms.content.image.models import ImageContent

    Page.register_extensions('datepublisher', 'translations') # Example set of extensions

    Page.register_templates({
        'title': _('Standard template'),
        'path': 'base.html',
        'regions': (
            ('main', _('Main content area')),
            ('sidebar', _('Sidebar'), 'inherited'),
            ),
        })

    Page.create_content_type(RichTextContent)
    Page.create_content_type(ImageContent, POSITION_CHOICES=(
        ('block', _('block')),
        ('left', _('left')),
        ('right', _('right')),
        ))


It will be a good idea most of the time to register the
:class:`~feincms.content.richtext.models.RichTextContent`
first, because it's the most used content type for many applications. The
content type dropdown will contain content types in the same order as they
were registered.

Please note that you should put these statements into a ``models.py`` file
which is executed at Django startup time, i.e. into a ``models.py`` file
contained in ``INSTALLED_APPS``.


Setting up the admin interface
==============================

The customized admin interface code is contained inside the :class:`ModelAdmin`
subclass, so you do not need to do anything special here. You only need to set
:data:`~feincms.settings.FEINCMS_ADMIN_MEDIA` as described in the installation documentation.

If you use the :class:`~feincms.content.richtext.models.RichTextContent`, you
need to download `TinyMCE <http://tinymce.moxiecode.com/>`_ and set
:data:`TINYMCE_JS_URL` to the absolute path to the main javascript file.


Wiring up the views
===================

Just add the following lines to your ``urls.py`` to get a catch-all URL pattern:

::

    urlpatterns += patterns(``,
        url(r'^$|^(.*)/$', 'feincms.views.base.handler'),
    )


If you want to define a page as home page for the whole site, you can give it
an :attr:`~Page.override_url` value of ``'/'``.

More information can be found in :ref:`integration`


Adding another content type
===========================

Imagine you've got a third-party gallery application and you'd like to include
excerpts of galleries inside your content. You'd need to write a :class:`GalleryContent`
base class and let FeinCMS create a model class for you with some important
attributes added.

::

    from django.db import models
    from django.template.loader import render_to_string
    from feincms.module.page.models import Page
    from gallery.models import Gallery

    class GalleryContent(models.Model):
        gallery = models.ForeignKey(Gallery)

        class Meta:
            abstract = True

        def render(self, **kwargs):
            return render_to_string('gallery/gallerycontent.html', {
                'images': self.gallery.image_set.order_by('?')[:5],
            })

    Page.create_content_type(GalleryContent)


The newly created :class:`GalleryContent` for :class:`~feincms.module.page.models.Page`
will live in the database table ``page_page_gallerycontent``.

It is generally recommended to make your model base class abstract, because
FeinCMS will create another class inheriting from your class, and you should
probably not use model inheritance if you don't know exactly that you'll need
it.


.. _page-extensions:

Page extension modules
======================

.. module:: feincms.module.page.extension

Extensions are a way to put often-used functionality easily accessible without
cluttering up the core page model for those who do not need them. The extensions
are standard python modules with a :func:`register` method which will be called
upon registering the extension. The :func:`register` method receives the
:class:`~feincms.module.page.models.Page` class itself and the model admin class
:class:`~feincms.module.page.models.PageAdmin` as arguments. The extensions can
be activated as follows::

     Page.register_extensions('navigation', 'titles', 'translations')


The following extensions are available currently:

* :mod:`~feincms.module.page.extension.changedate` --- Creation and modification dates

  Adds automatically maintained creation and modification date fields
  to the page.


* :mod:`~feincms.module.page.extension.datepublisher` --- Date-based publishing

  Adds publication date and end date fields to the page, thereby enabling the
  administrator to define a date range where a page will be available to
  website visitors.


* :mod:`~feincms.module.page.extension.navigation` --- Navigation extensions

  Adds navigation extensions to the page model. You can define subclasses of
  ``NavigationExtension``, which provide submenus to the navigation generation
  mechanism. See :ref:`page-ext-navigation` for more information on how to use
  this extension.


* :mod:`~feincms.module.page.extension.seo` --- Search engine optimization

  Adds fields to the page relevant for search engine optimization (SEO),
  currently only meta keywords and description.


* :mod:`~feincms.module.page.extension.symlinks` --- Symlinked content extension

  Sometimes you want to reuse all content from a page in another place. This
  extension lets you do that.


* :mod:`~feincms.module.page.extension.titles` --- Additional titles

  Adds additional title fields to the page model. You may not only define a
  single title for the page to be used in the navigation, the <title> tag and
  inside the content area, you are not only allowed to define different titles
  for the three uses but also enabld to define titles and subtitles for the
  content area.


* :mod:`~feincms.module.page.extension.translations` --- Page translations

  Adds a language field and a recursive translations many to many field to the
  page, so that you can define the language the page is in and assign
  translations. I am currently very unhappy with state of things concerning
  the definition of translations, so that extension might change somewhat too.
  This extension also adds new instructions to the setup_request method where
  the Django i18n tools are initialized with the language given on the page
  object.


Using page request processors
=============================

A request processor is a function that gets the currently selected page and the
request as parameters and returns either None (or nothing) or a HttpResponse.
All registered request processors are run before the page is actually rendered.
If the request processor indeed returns a :class:`HttpResponse`, further rendering of
the page is cut short and this response is returned immediately to the client.

This allows for various actions dependent on page and request, for example a
simple user access check can be implemented like this:

::

    def authenticated_request_processor(page, request):
        if not request.user.is_authenticated():
            return HttpResponseForbidden()

    Page.register_request_processors(authenticated_request_processor)


Using page response processors
==============================

Analogous to a request processor, a reponse processor runs after a page
has been rendered. It needs to accept the page, the request and the response
as parameters and may change the response (or throw an exception, but try
not to).

A reponse processor is the right place to tweak the returned http response
for whatever purposes you have in mind.

::

    def set_random_header_response_processor(page, request, response):
        response['X-Random-Number'] = 42

    Page.register_response_processors(set_random_header_response_processor)


ETag handling
=============

An ETag is a string that is associated with a page -- it should change if
(and only if) the page content itself has changed. Since a page's content
may depend on more than just the raw page data in the database (e.g. it
might list its children or a navigation tree or an excerpt from some other
place in the CMS alltogether), you are required to write an etag producing
method for the page.

::

    # Very stupid etag function, a page is supposed the unchanged as long
    # as its id and slug do not change. You definitely want something more
    # involved, like including last change dates or whatever.
    def my_etag(page, request):
        return 'PAGE-%d-%s' % ( page.id, page.slug )
    Page.etag = my_etag

    Page.register_request_processors(Page.etag_request_processor)
    Page.register_response_processors(Page.etag_response_processor)


Sitemaps
========

To create a sitemap that is automatically populated with all pages in your
Feincms site, add the following to your top-level urls.py:

::

    from feincms.module.page.sitemap import PageSitemap
    sitemaps = { 'pages' : PageSitemap }

    urlpatterns += (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps})

This will produce a default sitemap at the /sitemap.xml url. A sitemap can be
further customised by passing it appropriate parameters, like so:

::

    sitemaps = { 'pages' : PageSitemap(max_depth=2), }


The following parameters can be used to modify the behaviour of the sitemap:

* navigation_only -- if set to True, only pages that are in_navigation will appear
  in the site map.
* max_depth -- if set to a non-negative integer, will limit the sitemap generated
  to this page hierarchy depth.
* changefreq -- should be a string or callable specifiying the page update frequency,
  according to the sitemap protocol.



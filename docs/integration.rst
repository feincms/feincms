.. _integration:

=========================================
Integrating 3rd party apps into your site
=========================================

With FeinCMS come a set of standard views which you might want to check
out before starting to write your own.


Default page handler
====================

The default CMS handler view is ``feincms.views.cbv.handler``. You can
add the following as last line in your ``urls.py`` to make a catch-all
for any pages which were not matched before::

    from feincms.views.cbv.views import Handler
    handler = Handler.as_view()

    urlpatterns += patterns('',
        url(r'^$', handler, name='feincms_home'),
        url(r'^(.*)/$', handler, name='feincms_handler'),
    )

Note that this default handler can also take a keyword parameter ``path``
to specify which url to render. You can use that functionality to
implement a default page by adding another entry to your ``urls.py``::

    from feincms.views.cbv.views import Handler
    handler = Handler.as_view()

    ...
        url(r'^$', handler, {'path': '/rootpage'},
            name='feincms_home')
    ...


Please note that it's easier to include ``feincms.urls`` at the bottom
of your own URL patterns like this::

    # ...

    urlpatterns += patterns('',
        url(r'', include('feincms.urls')),
    )

The URLconf entry names ``feincms_home`` and ``feincms_handler`` must
both exist somewhere in your project. The standard ``feincms.urls``
contains definitions for both. If you want to provide your own view,
it's your responsability to create correct URLconf entries.


Generic and custom views
========================

If you use FeinCMS to manage your site, chances are that you still want
to use generic and/or custom views for certain parts. You probably still need a
``feincms_page`` object inside your template to generate the navigation and
render regions not managed by the generic views. The best way to ensure
the presence of a ``feincms_page`` instance in the template context is
to add ``feincms.context_processors.add_page_if_missing`` to your
``TEMPLATE_CONTEXT_PROCESSORS`` setting.


.. _integration-applicationcontent:

Integrating 3rd party apps
==========================

Third party apps such as django-registration can be integrated in the CMS
too. :class:`~feincms.content.application.models.ApplicationContent` lets you
delegate a subset of your page tree to a third party application. The only
thing you need is specifying a URLconf file which is used to determine which
pages exist below the integration point.


Adapting the 3rd party application for FeinCMS
----------------------------------------------

The integration mechanism is very flexible. It allows the website
administrator to add the application in multiple places or move the
integration point around at will. Obviously, this flexibility puts
several constraints on the application developer. It is therefore
probable, that you cannot just drop in a 3rd party application and
expect it to work. Modifications of ``urls.py`` and the templates
will be required.

The following examples all assume that we want to integrate a news
application into FeinCMS. The
:class:`~feincms.content.application.models.ApplicationContent` will
be added to the page at ``/news/``, but that's not too important really,
because the 3rd party app's assumption about where it will be integrated
can be too easily violated.

An example ``urls.py`` follows::

    from django.conf.urls import patterns, include, url
    from django.views.generic.detail import DetailView
    from django.views.generic.list import ListView
    from news.models import Entry


    urlpatterns = patterns('',
        url(r'^$', ListView.as_view(
            queryset=Entry.objects.all(),
            ), name='entry_list'),
        url(r'^(?P<slug>[^/]+)/$', DetailView.as_view(
            queryset=Entry.objects.all(),
            ), name='entry_detail'),
    )

Please note that you should not add the ``news/`` prefix here. You should
*not* reference this ``urls.py`` file anywhere in a ``include`` statement.


Registering the 3rd party application with FeinCMS' ``ApplicationContent``
--------------------------------------------------------------------------

It's as simple as that::

    from feincms.content.application.models import ApplicationContent
    from feincms.module.page.models import Page

    Page.create_content_type(ApplicationContent, APPLICATIONS=(
        ('news.urls', 'News application'),
        ))


Writing the models
------------------

Because the URLconf entries ``entry_list`` and ``entry_detail`` aren't
reachable through standard means (remember, they aren't ``include``\d
anywhere) it's not possible to use standard ``reverse`` calls to
determine the absolute URL of a news entry. FeinCMS provides its own
``app_reverse`` function (see :ref:`integration-reversing-urls` for
details) and ``permalink`` decorator mimicking the interface of
Django's standard functionality::


    from django.db import models
    from feincms.content.application import models as app_models

    class Entry(models.Model):
       title = models.CharField(max_length=200)
       slug = models.SlugField()
       description = models.TextField(blank=True)

       class Meta:
           ordering = ['-id']

       def __str__(self):
           return self.title

       @app_models.permalink
       def get_absolute_url(self):
           return ('entry_detail', 'news.urls', (), {
               'slug': self.slug,
               })


The only difference is that you do not only have to specify the view name
(``entry_detail``) but also the URLconf file (``news.urls``) for this
specific ``permalink`` decorator. The URLconf string must correspond to the
specification used in the ``APPLICATIONS`` list in the ``create_content_type``
call.

.. note::

   Previous FeinCMS versions only provided a monkey patched ``reverse``
   method with a slightly different syntax for reversing URLs. This
   behavior is still available and as of now (FeinCMS 1.5) still active
   by default. It is recommended to start using the new way right now
   and add ``FEINCMS_REVERSE_MONKEY_PATCH = False`` to your settings file.


Returning content from views
----------------------------

Three different types of return values can be handled by the application
content code:

* Unicode data (e.g. the return value of ``render_to_string``)
* ``HttpResponse`` instances
* A tuple consisting of two elements: A template instance, template name or list
  and a context ``dict``. More on this later under
  :ref:`integration-applicationcontent-inheritance20`


Unicode data is inserted verbatim into the output. ``HttpResponse`` instances
are returned directly to the client under the following circumstances:

* The HTTP status code differs from ``200 OK`` (Please note that 404 errors may
  be ignored if more than one content type with a ``process`` method exists on
  the current CMS page.)
* The resource was requested by ``XmlHttpRequest`` (that is, ``request.is_ajax``
  returns ``True``)
* The response was explicitly marked as ``standalone`` by the
  :func:`feincms.views.decorators.standalone` view decorator
  (made easier by mixing-in :class:`feincms.module.mixins.StandaloneView`)
* The mimetype of the response was not ``text/plain`` or ``text/html``

Otherwise, the content of the response is unpacked and inserted into the
CMS output as unicode data as if the view returned the content directly, not
wrapped into a ``HttpResponse`` instance.

If you want to customize this behavior, provide your own subclass of
``ApplicationContent`` with an overridden ``send_directly`` method. The
described behavior is only a sane default and might not fit everyone's
use case.

.. note::

   The string or response returned should not contain ``<html>`` or ``<body>``
   tags because this would invalidate the HTML code returned by FeinCMS.


.. _integration-applicationcontent-inheritance20:

Letting the application content use the full power of Django's template inheritance
-----------------------------------------------------------------------------------

If returning a simple unicode string is not enough and you'd like to modify
different blocks in the base template, you have to ensure two things:

* Use the class-based page handler. This is already the default if you include
  ``feincms.urls`` or ``feincms.views.cbv.urls``.
* Make sure your application views use the third return value type described
  above: A tuple consisting of a template and a context ``dict``.

The news application views would then look as follows. Please note the absence
of any template rendering calls:

``views.py``::

    from django.shortcuts import get_object_or_404
    from news.models import Entry

    def entry_list(request):
        # Pagination should probably be added here
        return 'news/entry_list.html', {'object_list': Entry.objects.all()}

    def entry_detail(request, slug):
        return 'news/entry_detail', {'object': get_object_or_404(Entry, slug=slug)}

``urls.py``::

    from django.conf.urls import patterns, include, url

    urlpatterns = patterns('news.views',
        url(r'^$', 'entry_list', name='entry_list'),
        url(r'^(?P<slug>[^/]+)/$', 'entry_detail', name='entry_detail'),
    )


The two templates referenced, ``news/entry_list.html`` and
``news/entry_detail.html``, should now extend a base template. The recommended
notation is as follows::

    {% extends feincms_page.template.path|default:"base.html" %}

    {% block ... %}
    {# more content snipped #}


This ensures that the the selected CMS template is still used when rendering
content.

.. note::

   Older versions of FeinCMS only offered fragments for a similar purpose. They
   are still suported, but it's recommended you switch over to this style instead.

.. warning::

   If you add two application content blocks on the same page and both use this
   mechanism, the later 'wins'.

.. _integration-reversing-urls:

More on reversing URLs
----------------------

Application content-aware URL reversing is available both for Python and
Django template code.

The function works almost like Django's own ``reverse()`` method except
that it resolves URLs from application contents. The second argument,
``urlconf``, has to correspond to the URLconf parameter passed in the
``APPLICATIONS`` list to ``Page.create_content_type``::

    from feincms.content.application.models import app_reverse
    app_reverse('mymodel-detail', 'myapp.urls', args=...)

or::

    app_reverse('mymodel-detail', 'myapp.urls', kwargs=...)


The template tag has to be loaded from the ``applicationcontent_tags``
template tag library first::

    {% load applicationcontent_tags %}
    {% app_reverse "mymodel_detail" "myapp.urls" arg1 arg2 %}

or::

    {% load applicationcontent_tags %}
    {% app_reverse "mymodel_detail" "myapp.urls" name1=value1 name2=value2 %}

Storing the URL in a context variable is supported too::

    {% load applicationcontent_tags %}
    {% app_reverse "mymodel_detail" "myapp.urls" arg1 arg2 as url %}

Inside the app (in this case, inside the views defined in ``myapp.urls``),
you can also pass the current request instance instead of the URLconf
name.

If an application has been added several times to the same page tree,
``app_reverse`` tries to find the best match. The logic is contained inside
``ApplicationContent.closest_match``, and can be overridden by subclassing
the application content type. The default implementation only takes the current
language into account, which is mostly helpful when you're using the
translations page extension.


Additional customization possibilities
--------------------------------------

The ``ApplicationContent`` offers additional customization possibilites for those who
need them. All of these must be specified in the ``APPLICATIONS`` argument to
``create_content_type``.

* ``urls``: Making it easier to swap the URLconf file:

  You might want to use logical names instead of URLconf paths when you create
  your content types, so that the ``ApplicationContent`` apps aren't tied to
  a particular ``urls.py`` file. This is useful if you want to override a few
  URLs from a 3rd party application, f.e. replace ``registration.urls`` with
  ``yourapp.registration_urls``::

      Page.create_content_type(ApplicationContent, APPLICATIONS=(
        ('registration', 'Account creation and management', {
            'urls': 'yourapp.registration_urls',
            }),
        )

* ``admin_fields``: Adding more fields to the application content interface:

  Some application contents might require additional configuration parameters
  which should be modifyable by the website administrator. ``admin_fields`` to
  the rescue!

  ::

      def registration_admin_fields(form, *args, **kwargs):
        return {
            'exclusive_subpages': forms.BooleanField(
                label=_('Exclusive subpages'),
                required=False,
                initial=form.instance.parameters.get('exclusive_subpages', True),
                help_text=_('Exclude everything other than the application\'s content when rendering subpages.'),
                ),
            }

      Page.create_content_type(ApplicationContent, APPLICATIONS=(
        ('registration', 'Account creation and management', {
            'urls': 'yourapp.registration_urls',
            'admin_fields': registration_admin_fields,
            }),
        )

  The form fields will only be visible after saving the ``ApplicationContent``
  for the first time. They are stored inside a JSON-encoded field. The values
  are added to the template context indirectly when rendering the main template
  by adding them to ``request._feincms_extra_context``.

* ``path_mapper``: Customize URL processing by altering the perceived path of the page:

  The applicaton content uses the remainder of the URL to resolve the view inside
  the 3rd party application by default. This works fine most of the time, sometimes
  you want to alter the perceived path without modifying the URLconf file itself.

  If provided, the ``path_mapper`` receives the three arguments, ``request.path``,
  the URL of the current page and all application parameters, and must return
  a tuple consisting of the path to resolve inside the application content and
  the path the current page is supposed to have.

  This ``path_mapper`` function can be used to do things like rewrite the path so
  you can pretend that an app is anchored deeper than it actually is (e.g.
  /path/to/page is treated as "/<slug>/" using a parameter value rather
  than "/" by the embedded app)

* ``view_wrapper``: Decorate every view inside the application content:

  If the customization possibilites above aren't sufficient, ``view_wrapper``
  can be used to decorate each and every view inside the application content
  with your own function. The function specified with ``view_wrapper`` receives
  an additional parameters besides the view itself and any arguments or
  keyword arguments the URLconf contains, ``appcontent_parameters`` containing
  the application content configuration.


.. _page-ext-navigation:

Letting 3rd party apps define navigation entries
------------------------------------------------

Short answer: You need the ``feincms.module.page.extensions.navigation``
extension module. Activate it like this::

    Page.register_extensions('feincms.module.page.extensions.navigation')


Please note however, that this call needs to come after all
``NavigationExtension`` subclasses have been processed, because otherwise they
will not be available for selection in the page administration! (Yes, this is
lame and yes, this is going to change as soon as we find a
better solution. In the meantime, stick your subclass definition before
the register_extensions call.)

Because the use cases for extended navigations are so different, FeinCMS
does not go to great lengths trying to cover them all. What it does though
is to let you execute code to filter, replace or add navigation entries when
generating a list of navigation entries.

If you have a blog and you want to display the blog categories as subnavigation
entries, you could do it as follows:

#. Create a navigation extension for the blog categories

#. Assign this navigation extension to the CMS page where you want these navigation entries to appear

You don't need to do anything else as long as you use the built-in
``feincms_nav`` template tag -- it knows how to handle extended navigations.

::

    from feincms.module.page.extensions.navigation import NavigationExtension, PagePretender

    class BlogCategoriesNavigationExtension(NavigationExtension):
        name = _('blog categories')

        def children(self, page, **kwargs):
            for category in Category.objects.all():
                yield PagePretender(
                    title=category.name,
                    url=category.get_absolute_url(),
                    )

    class PassthroughExtension(NavigationExtension):
        name = 'passthrough extension'

        def children(self, page, **kwargs):
            for p in page.children.in_navigation():
                yield p

    Page.register_extensions('feincms.module.page.extensions.navigation')

Note that the objects returned should at least try to mimic a real page so
navigation template tags as ``siblings_along_path_to`` and friends continue
to work, ie. at least the following attributes should exist:

::

    title     = '(whatever)'
    url       = '(whatever)'

    # Attributes that MPTT assumes to exist
    parent_id = page.id
    tree_id   = page.tree_id
    level     = page.level+1
    lft       = page.lft
    rght      = page.rght



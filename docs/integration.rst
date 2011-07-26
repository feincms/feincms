.. _integration:

=========================================
Integrating 3rd party apps into your site
=========================================

With FeinCMS come a set of standard views which you might want to check
out before starting to write your own. Included is a standard view for
pages, and a set of generic view drop-in replacements which know about
the CMS.


Default page handler
====================

The default CMS handler view is ``feincms.views.base.handler``. You can
add the following as last line in your ``urls.py`` to make a catch-all
for any pages which were not matched before:

::

    urlpatterns += patterns('',
        url(r'^$', base.handler, name='feincms_home'),
        url(r'^(.*)/$', base.handler, name='feincms_handler'),
    )

Note that this default handler can also take a keyword parameter ``path``
to specify which url to render. You can use that functionality to
implement a default page by adding another entry to your ``urls.py``:

::

        url(r'^$', 'feincms.views.base.handler', {'path': '/rootpage'},
            name='feincms_home')


Please note that it's easier to include ``feincms.urls`` at the bottom
of your own URL patterns like this::

    # ...

    urlpatterns += patterns('',
        url(r'', include('feincms.urls')),
    )


Generic views
=============

If you use FeinCMS to manage your site, chances are that you still want
to use generic views for certain parts. You probably still need a
``feincms_page`` object inside your template to generate the navigation and
render regions not managed by the generic views. By simply replacing
:mod:`django.views.generic` with :mod:`feincms.views.generic` in your
``urls.py``. The page which
most closely matches the current request URI will be passed into the
template by automatically adding ``feincms_page`` to the ``extra_context``
generic view argument.


.. _integration-applicationcontent:

Integrating 3rd party apps
==========================

The :class:`~feincms.content.application.models.ApplicationContent` will
help you with this.

The plugin/content type needs a URLconf and uses resolve and a patched
reverse to integrate the application into the CMS. The advantages are
that there is no modification of the ROOT_URLCONF necessary when
moving the integration point for the 3rd party application around. On
the downside, the application's template has less control over the
base template and views inside the 3rd party app cannot be reversed
from outside the ApplicationContent renderer. The bigger flexibility
in choosing the integration point comes with a cost when it comes to
rendering the content from the 3rd party app.

.. warning::

   The monkey patch for ``django.core.urlresolvers.reverse`` contained
   in the ``ApplicationContent`` code has to happen "early enough". If
   ``reverse`` is unable to determine URLs for views integrated through
   ``ApplicationContent`` you have to move the application content code
   import to an earlier place (f.e. on the first line of your main
   ``models.py`` or even in your ``urls.py`` (barring circular import
   problems).

   This might change if we find a better way to solve this or if
   Django allows us to poke deeper into the URL resolving/reversing
   machinery.


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

    from django.conf.urls.defaults import *
    from news.models import Entry

    entry_dict = {'queryset': Entry.objects.all()}

    urlpatterns = patterns('',
       url(r'^$',
           'django.views.generic.list_detail.object_list',
           entry_dict,
           name='entry_list'),
       url(r'^(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<slug>[^/]+)/',
           'django.views.generic.date_based.object_detail',
           dict(entry_dict, **{'date_field': 'published_date', 'month_format': '%m', 'slug_field': 'slug'}),
           name='entry_detail'),
    )


Please note that you should not add the ``news/`` prefix here unless
you know exactly what you are doing. Furthermore, this ``urls.py`` is
incomplete -- for a real world implementation, you'd need to add yearly,
monthly and daily archive views too. Furthermore, you should *not* include
this ``urls.py`` file anywhere accessible from your ``ROOT_URLCONF``.

If you write your view methods yourself instead of using generic views, you
should not construct whole response objects, but return the content as a unicode
string. It does not hurt to encapsulate the content inside a response object,
it's simply not worth it because the application content will have to extract
the content from the response and throw the response object away anyway.

The :class:`~feincms.content.application.models.ApplicationContent` patches
the standard Django ``reverse`` function, so that ``reverse`` and the
``{% url %}`` template tag works as expected inside the application
content render method. Therefore, :meth:`News.get_absolute_url` is
absolutely standard. ``models.py``::

    from datetime import datetime
    from django.db import models

    class Entry(models.Model):
       published_date = models.DateField()
       title = models.CharField(max_length=200)
       slug = models.SlugField()
       description = models.TextField(blank=True)

       class Meta:
           get_latest_by = 'published_date'
           ordering = ['-published_date']

       def __unicode__(self):
           return self.title

       @models.permalink
       def get_absolute_url(self):
           return ('entry_detail', (), {
               'year': self.published_date.strftime('%Y'),
               'month': self.published_date.strftime('%m'),
               'day': self.published_date.strftime('%d'),
               'slug': self.slug,
               })


Writing the templates for the application
-----------------------------------------

Nothing special here. The only thing you have to avoid is adding ``<html>`` or
``<body>`` tags and such, because you're only rendering content for a single
content block, not the whole page. An example ``news/entry_detail.html`` follows::

    <div class="entry">
       <h2>{{ object.title }}</h2>
       <span class="date">{{ object.published_date|date:"d.m.Y" }}</span>

       {{ object.description|linebreaks }}
    </div>

And an example ``news/entry_list.html``::

    {% for entry in object_list %}
        <div class="entry">
            {% ifchanged %}<div class="date">{{ entry.published_date|date:"d.m.Y" }}</div>{% endifchanged %}
            <h2><a href="{{ entry.get_absolute_url }}">{{ entry.title }}</a></h2>
        </div>
    {% endfor %}


Registering and integrating the 3rd party application
-----------------------------------------------------

First, you need to create the content type::

    from feincms.content.application.models import ApplicationContent
    from feincms.module.page.models import Page

    Page.create_content_type(ApplicationContent, APPLICATIONS=(
        ('news.urls', 'News application'),
        ))

Your base template does not have to be structured differently just because
you are using application contents now. You must use the bundled FeinCMS
template tags though, because the application content needs the request
object::

    {% extends "base.html" %}

    {% load feincms_tags %}

    {% block content %}
       {% feincms_render_region feincms_page "main" request %}
    {% endblock %}

Please note that this necessitates the use of
``django.core.context_processors.request``::

    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.auth',
        'django.core.context_processors.debug',
        'django.core.context_processors.i18n',
        'django.core.context_processors.media',
        'django.core.context_processors.request',
    )


The 3rd party application might know how to handle more than one URL (the example
news application does). These subpages won't necessarily exist as page instances
in the tree, the standard view knows how to handle this case.


.. _integration-applicationcontent-morecontrol:

Letting the application content control more than one region in the parent template
-----------------------------------------------------------------------------------

The output of the third party app is not strictly constrained to the region;
you can pass additional fragments around, for example to extend the page title
with content from the 3rd party application. Suppose we'd like to add the news
title to the title tag. Add the following lines to your ``news/entry_detail.html``::

    {% load applicationcontent_tags %}
    {% fragment request "title" %}{{ object.translation.title }} - {% endfragment %}

And read the fragment inside your base template::

    {% extends "base.html" %}

    {% load applicationcontent_tags feincms_page_tags %}

    {% block title %}{% get_fragment request "title" %} - {{ feincms_page.title }} - {{ block.super }}{% endblock %}

    {% block content %}
       {% feincms_render_region feincms_page "main" request %}
    {% endblock %}


Returning responses from the embedded application without wrapping them inside the CMS template
-----------------------------------------------------------------------------------------------

If the 3rd party application returns a response with status code different from
200, the standard view :func:`feincms.views.base.handler` returns
the response verbatim. The same is true if the 3rd party application returns
a response and ``request.is_ajax()`` is ``True`` or if the application content
returns a HttpResponse with the ``standalone`` attribute set to True.

For example, an application can return an non-html export file -- in that case
you don't really want the CMS to decorate the data file with the web html templates:

::

    from feincms.views.decorators import standalone

    @standalone
    def my_view(request):
        ...
        xls_data = ... whatever ...
        return HttpResponse(xls_data, content_type="application/msexcel")


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

Short answer: You need the ``navigation`` extension module. Activate it like
this::

    Page.register_extensions('navigation')


Please note however, that this call needs to come after all
``NavigationExtension`` subclasses have been processed, because otherwise they
will not be available for selection in the page administration! (Yes, this is
lame and yes, this is going to change as soon as I find the time to whip up a
better solution.)

Because the use cases for extended navigations are so different, FeinCMS
does not go to great lengths trying to cover them all. What it does though
is to let you execute code to filter, replace or add navigation entries when
generating a list of navigation entries.

If you have a blog and you want to display the blog categories as subnavigation
entries, you could do it as follows:

#. Create a navigation extension for the blog categories

#. Assign this navigation extension to the CMS page where you want these navigation entries to appear

You don't need to do anything else as long as you use the built-in
``feincms_navigation`` template tag -- it knows how to handle extended navigations.

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

    Page.register_extensions('navigation')

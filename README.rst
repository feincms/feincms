========================================
FeinCMS - An extensible Django-based CMS
========================================

When was the last time, that a pre-built software package you wanted to
use got many things right, but in the end, you still needed to modify
the core parts of the code just because it wasn't (easily) possible to
customize the way, a certain part of the system behaved?

Django came to rescue all of us, who were not happy with either doing
everything on our own or customizing another software package until it
was impossible to update.

The biggest strength of a framework-like design is, that it tries not
to have a too strong view of what the user should do. It should make some
things easy, but just GET OUT OF THE WAY most of the time.

Just after discovering the benefits of a framework-like approach to
software design, we fall back into the rewrite everything all the time
mindset and build a CMS which has very strong views how content should
be structured. One rich text area, a media library and some templates,
and we have a simple CMS which will be good enough for many pages. But
what if we want more? If we want to be able to add custom content? What
if the user can't be trusted to resize images before uploading them?
What if you'd like to add a gallery somewhere in between other content?
What if the user should be able to administer not only the main content,
but also a sidebar, the footer?

With FeinCMS, this does not sound too good to be true anymore. And it's
not even complicated.


FeinCMS is an extremely stupid content management system. It knows
nothing about content -- just enough to create an admin interface for
your own page content types. It lets you reorder page content blocks
using a drag-drop interface, and you can add as many content blocks
to a region (f.e. the sidebar, the main content region or something
else which I haven't thought of yet). It provides helper functions,
which provide ordered lists of page content blocks. That's all.


Adding your own content types is extremely easy. Do you like textile
that much, that you'd rather die than using a rich text editor?
Then add the following code to your project, and you can go on using the
CMS without being forced to use whatever the developers deemed best:

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


That's it. Not even ten code lines for your own page content type.



Getting started
===============

Visit these sites
-----------------

* FeinCMS Website: http://www.feinheit.ch/labs/feincms-django-cms/
* Read the documentation: http://www.feinheit.ch/media/labs/feincms/
* See the google groups page at http://groups.google.com/group/django-feincms
* FeinCMS on github: https://github.com/feincms/feincms/

Quickstart
----------

You can find a short quickstart guide at QUICKSTART.rst

Optional Packages
-----------------

* `pytidylib <http://countergram.com/open-source/pytidylib/>`_ can be
  installed to perform HTML validation and cleanup using `HTML Tidy
  <http://tidy.sourceforge.net>`_ while editing content. Install pytidylib and
  add ``FEINCMS_TIDY_HTML = True`` to your settings.py.

* Alternately, `lxml <http://pypi.python.org/pypi/lxml>`_ can be installed to perform
  silent HTML cleanup to remove non-standard markup while editing content.
  Install lxml and add ``cleanse=True`` when you register ``RichTextContent``
  or ``SectionContent``::

    RichTextContentType = Page.create_content_type(RichTextContent, cleanse=True)

Repository branches
-------------------

The FeinCMS repository on github has several branches. Their purpose and
rewinding policies are described below.

* ``maint``: Maintenance branch for the second-newest version of FeinCMS.
* ``master``: Stable version of FeinCMS.

``master`` and ``maint`` are never rebased or rewound.

* ``next``: Upcoming version of FeinCMS. This branch is rarely rebased
  if ever, but this might happen. A note will be sent to the official
  mailing list whenever ``next`` has been rebased.
* ``pu`` or feature branches are used for short-lived projects. These
  branches aren't guaranteed to stay around and are not meant to be
  deployed into production environments.

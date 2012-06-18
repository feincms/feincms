.. _installation:

=========================
Installation instructions
=========================

Installation
============

This document describes the steps needed to get FeinCMS up and running.

FeinCMS is based on Django, so you need a working Django_ installation
first. The minimum support version of Django_ is the 1.4 line of releases.

You can download a stable release of FeinCMS using ``pip``::

    $ pip install feincms

Pip will install feincms and its dependencies. It will however not install
documentation, tests or the example project which comes with the development version,
which you can download using the Git_ version control system::

    $ git clone git://github.com/feincms/feincms.git

Feincms, some content types or cleaning modules are dependent on the following apps, which are installed when using pip:
lxml_, feedparser_, PIL_, django-mptt_ and BeautifulSoup_.

However, django-tagging_ is not installed because the blog module that uses it is merely a proof of
concept. If you are looking to implement a blog, check out elephantblog_.

You will also need a Javascript WYSIWYG editor of your choice (Not included).
TinyMCE_ works out of the box and is recommended.


.. _Django: http://www.djangoproject.com/
.. _Git: http://git-scm.com/
.. _Subversion: http://subversion.tigris.org/
.. _django-mptt: http://github.com/django-mptt/django-mptt/
.. _django-tagging: http://code.google.com/p/django-tagging/
.. _lxml: http://codespeak.net/lxml/
.. _feedparser: http://www.feedparser.org/
.. _PIL: http://www.pythonware.com/products/pil/
.. _BeautifulSoup: http://pypi.python.org/pypi/BeautifulSoup/3.2.1
.. _elephantblog: http://github.com/feincms/feincms-elephantblog
.. _TinyMCE: http://www.tinymce.com/
.. _CKEditor: http://ckeditor.com/


Configuration
=============

There isn't much left to do apart from adding a few entries to ``INSTALLED_APPS``,
most commonly you'll want to add ``feincms``, ``mptt``, ``feincms.module.page`` and
``feincms.module.medialibrary``.
The customized administration interface needs some media and javascript
libraries which you have to make available to the browser. FeinCMS uses Django's
``django.contrib.staticfiles`` application for this purpose, the media files will
be picked up automatically by the ``collectstatic`` management command.

If your website is multi-language you have to define ``LANGUAGES`` in the settings_.

Please note that the ``feincms`` module will not create or need any database
tables, but you need to put it into ``INSTALLED_APPS`` because otherwise the
templates in ``feincms/templates/`` will not be found by the template loader.

The tools contained in FeinCMS can be used for many CMS-related
activities. The most common use of a CMS is to manage a hierarchy of
pages and this is the most advanced module of FeinCMS too. Please
proceed to :ref:`page` to find out how you can get the page module
up and running.

.. _settings: https://docs.djangoproject.com/en/dev/topics/i18n/translation/#how-django-discovers-language-preference
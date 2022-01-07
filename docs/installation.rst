.. _installation:

=========================
Installation instructions
=========================

Installation
============

This document describes the steps needed to install FeinCMS.

FeinCMS requires a working installation of Django_ version 1.7 or better
See the Django_ documentation for how to install and configure Django.

You can download a stable release of FeinCMS using ``pip``. Pip will install
feincms and its dependencies. Dependencies which are automatically installed
are: feedparser_, Pillow_ and django-mptt_. For outdated versions of
Django the best place to find supported combinations of library versions is the
`Travis CI build configuration
<https://github.com/feincms/feincms/blob/master/.travis.yml>`_.

    $ pip install feincms

In order to install documentation and tests install from the Git_ repository
instead::

    $ git clone git://github.com/feincms/feincms.git

Please be aware that feincms3 is being developed as a separate, new project.
For new CMS projects I’m more likely to use django-content-editor and feincms3.
You can read more about feincms3 on https://feincms3.readthedocs.io/en/latest/

If you are looking to implement a blog, check out elephantblog_.

You will also need a Javascript WYSIWYG editor of your choice (Not included).
TinyMCE_ and CKEditor_ work out of the box and are recommended.


.. _Django: http://www.djangoproject.com/
.. _Git: http://git-scm.com/
.. _Subversion: http://subversion.tigris.org/
.. _django-mptt: http://github.com/django-mptt/django-mptt/
.. _feedparser: http://www.feedparser.org/
.. _Pillow: https://pypi.python.org/pypi/Pillow/
.. _elephantblog: http://github.com/feincms/feincms-elephantblog
.. _TinyMCE: http://www.tinymce.com/
.. _CKEditor: http://ckeditor.com/


Configuration
=============

There isn't much left to do apart from adding a few entries to
``INSTALLED_APPS``. Most commonly you'll want to add::

    feincms,
    mptt,
    feincms.module.page,
    feincms.module.medialibrary

The customized administration interface needs some media and javascript
libraries which you have to make available to the browser. FeinCMS uses
Django's ``django.contrib.staticfiles`` application for this purpose. The media
files will be picked up automatically by the ``collectstatic`` management
command.

If your website is multi-language you have to define ``LANGUAGES`` in the
settings_.

Please note that the ``feincms`` module will not create or need any database
tables, but you need to put it into ``INSTALLED_APPS`` because otherwise the
templates in ``feincms/templates/`` will not be found by the template loader.

The tools contained in FeinCMS can be used for many CMS-related
activities. The most common use of a CMS is to manage a hierarchy of
pages and this is the most advanced module of FeinCMS too. Please
proceed to :ref:`page` to find out how you can get the page module
up and running.

.. _settings: https://docs.djangoproject.com/en/dev/ref/settings/#languages

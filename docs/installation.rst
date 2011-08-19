.. _installation:

=========================
Installation instructions
=========================

Installation
============

This document describes the steps needed to get FeinCMS up and running.

FeinCMS is based on Django, so you need a working Django_ installation
first. The minimum support version of Django_ is the 1.2 line of releases.

You can download a stable release of FeinCMS using ``easy_install``::

    $ sudo easy_install feincms

Please note that the package installable with ``easy_install`` only
contains the files needed to run FeinCMS. It does not include documentation,
tests or the example project which comes with the development version,
which you can download using the Git_ version control system::

    $ git clone git://github.com/feincms/feincms.git

In addition, you will need a django-mptt_ installation.

Finally, some content types or extensions require recent versions of
lxml_, django-tagging_, feedparser_ and the python imaging library PIL_
(PIL_ is actually a dependency of Django_'s ImageField).


.. _Django: http://www.djangoproject.com/
.. _Git: http://git-scm.com/
.. _Subversion: http://subversion.tigris.org/
.. _django-mptt: http://github.com/django-mptt/django-mptt/
.. _django-tagging: http://code.google.com/p/django-tagging/
.. _lxml: http://codespeak.net/lxml/
.. _feedparser: http://www.feedparser.org/
.. _PIL: http://www.pythonware.com/products/pil/


Configuration
=============

There isn't much left to do apart from adding ``feincms`` to ``INSTALLED_APPS``.
The customized administration interface needs some media and javascript
libraries which you have to make available to the browser. If you use Django 1.3's
``django.contrib.staticfiles`` application, the media files will be picked up
automatically by the ``collectstatic`` management command. If you use ``/static/``
as ``STATIC_URL``, all is fine. Otherwise you have to set ``FEINCMS_ADMIN_MEDIA``
to the path where the FeinCMS media files can be found.

If you use an older version of Django, publish the files in the folder
``feincms/static/feincms/`` somewhere on your site and set ``FEINCMS_ADMIN_MEDIA``
to the location.

Please note that the ``feincms`` module will not create or need any database
tables, but you need to put it into ``INSTALLED_APPS`` because otherwise the
templates in ``feincms/templates/`` will not be found by the template loader.

The tools contained in FeinCMS can be used for many CMS-related
activities. The most common use of a CMS is to manage a hierarchy of
pages and this is the most advanced module of FeinCMS too. Please
proceed to :ref:`page` to find out how you can get the page module
up and running.

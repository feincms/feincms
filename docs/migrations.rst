.. _migrations:

======================================
Database migration support for FeinCMS
======================================


FeinCMS itself does not come with any migrations. It does not have to: Its
core models haven't changed for several versions now. This does not mean
migrations aren't supported. You are free to use either Django's builtin
migrations support, or also South if you're stuck with Django versions older
than 1.6.

Django's builtin migrations
===========================

* Create a new folder in your app with an empty ``__init__.py`` inside.
* Add the following configuration to your ``settings.py``::

    MIGRATION_MODULES = {
        'page': 'yourapp.migrate.page',
        'medialibrary': 'yourapp.migrate.medialibrary',
    }

.. warning::

   You **must not** use ``migrations`` as folder name for the FeinCMS
   migrations, otherwise Django and/or South **will** get confused.


For those still using South
===========================

If you don't know what South_ is you should probably go and read about
it right now!


The following steps should be sufficient to get up and running with South_
in your project:

.. _South: http://south.aeracode.org/

* Put a copy of South somewhere on your ``PYTHONPATH``, with ``pip``, ``hg``
  or whatever pleases you most.
* Add ``'south'`` to ``INSTALLED_APPS``.
* Create a new folder in your app with an empty ``__init__.py`` file inside,
  e.g. ``yourapp/migrate/``.
* Add the following configuration variable to your ``settings.py``::

      SOUTH_MIGRATION_MODULES = {
          'page': 'yourapp.migrate.page',
          'medialibrary': 'yourapp.migrate.medialibrary',
      }

* Run ``./manage.py convert_to_south page`` and
  ``./manage.py convert_to_south medialibrary``
* That's it!

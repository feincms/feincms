.. _migrations:

=================================================
Database migration support for FeinCMS with South
=================================================

If you don't know what South_ is you should probably go and read about
it right now!

.. _South: http://south.aeracode.org/


FeinCMS itself does not come with any migrations. It does not have to: Its
core models haven't changed for several versions now. This does not mean South
isn't supported! You are free to use South to manage FeinCMS' models which
is a very useful technique especially if you are using :ref:`page-extensions`.

The following steps should be sufficient to get up and running with South
in your project:

* Put a copy of South somewhere on your ``PYTHONPATH``, with ``pip``, ``hg``
  or whatever pleases you most.
* Add ``'south'`` to ``INSTALLED_APPS``.
* Create a new folder in your app with an empty ``__init__.py`` file inside,
  e.g. ``yourapp/migrate/``.
* Add the following configuration variable to your ``settings.py``::

      SOUTH_MIGRATION_MODULES = {
          'page': 'yourapp.migrate.page',
          'medialibrary': 'yourapp.migrate.medialibrary', # if you are using the medialibrary
                                                          # which comes with FeinCMS
          }

* Run ``./manage.py convert_to_south page`` and ``./manage.py convert_to_south medialibrary``
* That's it!

.. warning::

   You **must not** use ``migrations`` as folder name for the FeinCMS
   migrations, otherwise South **will** get confused.

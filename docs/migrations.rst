.. _migrations:

======================================
Database migration support for FeinCMS
======================================


FeinCMS itself does not come with any migrations. It is recommended that you
add migrations for FeinCMS models yourself inside your project.


Django's builtin migrations
===========================

This guide assumes that you are using both the page and the medialibrary
module from FeinCMS. Simply leave out medialibrary if unused.

* Create a new folder named ``migrate`` in your app with an empty
  ``__init__.py`` inside.
* Add the following configuration to your ``settings.py``::

    MIGRATION_MODULES = {
        'page': 'yourapp.migrate.page',
        'medialibrary': 'yourapp.migrate.medialibrary',
    }

.. warning::

   You **must not** use ``migrations`` as folder name for the FeinCMS
   migrations, otherwise Django **will** get confused.

* Create initial migrations and apply them::

    ./manage.py makemigrations medialibrary
    ./manage.py makemigrations page
    ./manage.py migrate

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

  ``makemigrations`` creates the ``yourapp/migrate/page/`` and
  ``yourapp/migrate/medialibrary/`` packages (including their
  ``__init__.py`` files) automatically. Run it before anything else, since
  other management commands such as ``runserver`` fail with an
  ``ImportError`` as long as the modules referenced in
  ``MIGRATION_MODULES`` do not exist yet.
* Run ``makemigrations`` again whenever you add extensions or content types
  to the page or medialibrary models, and commit the generated migrations
  to your repository.

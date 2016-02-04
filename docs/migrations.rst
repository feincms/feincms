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

* Create a new folder in your app with an empty ``__init__.py`` inside. Call it ``migrate``.
* Create a new folder inside migrate again with an empty ``__init__.py`` inside. Call it ``page``.
* Create a new folder inside migrate again with an empty ``__init__.py`` inside. Call it ``medialibrary``.
* Add the following configuration to your ``settings.py``::

    MIGRATION_MODULES = {
        'page': 'yourapp.migrate.page',
        'medialibrary': 'yourapp.migrate.medialibrary',
    }

Create the initial migrations::

    python manage.py makemigrations
    
If you have run syncdb then the tables will already exist and you will need to fake the inital migrations, otherwise you will need to run them.

Run the migrations::

    python manage.py migrate
    
Or fake the migrations (the most likely situation)::

    python manage.py migrate --fake-initial
    
Now if you create a new extension you will need to create a migration to add the field(s) to Page or whatever model you ``register_extensions()`` your extension to.

I have not been able to use ``python manage.py makemigrations`` to make the migration for me since as soon as I registered my extension I got a database transaction error when trying to run makemigration. To create a migration to add a field to the Page model create a file within the yourapp/migrate/page folder, this should be called something like ``0002_add_new_field.py`` where the numbering follows on from the last migration the rest of the filename can be descriptive to what the migration is doing.

Example migration code::

    # -*- coding: utf-8 -*-
    from __future__ import unicode_literals
    
    from django.db import models, migrations
    
    
    class Migration(migrations.Migration):
    
        dependencies = [
            ('page', '0001_initial'),
        ]
    
        operations = [
            migrations.AddField(
                model_name='page',
                name='[NEW_COLUMN_NAME]',
                field=models.[FIELD_TYPE]([OPTIONS HERE])
            )
        ]

Obviously you will need to replace ``[NEW_COLUMN_NAME]`` with the name of your new column and ``[FIELD_TYPE]`` with the correct field type eg. ``CharField`` and ``[OPTIONS HERE]`` with the options. These details must be the same as in your extension's ``handle_model()`` code, you should be able to just copy the whole field definition from the ``self.model.add_to_class()`` call.

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

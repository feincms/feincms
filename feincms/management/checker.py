from django.core.management.color import color_style
from django.db import connection


def check_database_schema(cls, module_name):
    """
    Returns a function which inspects the database table of the passed class.
    It checks whether all fields in the model are available on the database
    too. This is especially helpful for models with an extension mechanism,
    where the extension might be activated after syncdb has been run for the
    first time.

    Please note that you have to connect the return value using strong
    references. Here's an example how to do this::

        signals.post_syncdb.connect(check_database_schema(Page, __name__), weak=False)

    (Yes, this is a weak attempt at a substitute for South until we find
    a way to make South work with FeinCMS' dynamic model creation.)
    """

    def _fn(sender, **kwargs):
        if sender.__name__ != module_name:
            return

        cursor = connection.cursor()

        existing_columns = [row[0] for row in \
            connection.introspection.get_table_description(cursor, cls._meta.db_table)]

        missing_columns = []

        for field in cls._meta.fields:
            if field.column not in existing_columns:
                missing_columns.append(field)

        if not missing_columns:
            return

        style = color_style()

        print style.ERROR('The following columns seem to be missing in the database table %s:' % cls._meta.db_table)
        for field in missing_columns:
            print u'%s:%s%s' % (
                style.SQL_KEYWORD(field.column),
                ' ' * (25 - len(field.column)),
                u'%s.%s' % (field.__class__.__module__, field.__class__.__name__),
                )

        print style.NOTICE('\nPlease consult the output of `python manage.py sql %s` to'
            ' find out what the correct column types are. (Or use south, which is what'
            ' you should be doing anyway.)\n' % (
            cls._meta.app_label,
            ))
    return _fn

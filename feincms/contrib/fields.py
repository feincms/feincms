from django import forms
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import simplejson as json

class JSONFormField(forms.fields.CharField):
    def clean(self, value, *args, **kwargs):
        if value:
            try:
                # Run the value through JSON so we can normalize formatting and at least learn about malformed data:
                value = json.dumps(json.loads(value), cls=DjangoJSONEncoder)
            except ValueError:
                raise forms.ValidationError("Invalid JSON data!")

        return super(JSONFormField, self).clean(value, *args, **kwargs)

class JSONField(models.TextField):
    """
    TextField which transparently serializes/unserializes JSON objects

    See:
    http://www.djangosnippets.org/snippets/1478/
    """

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    formfield = JSONFormField

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if isinstance(value, dict):
            return value
        elif isinstance(value, basestring):
            return json.loads(value)
        else:
            assert value is None
            return {}

    def get_db_prep_save(self, value):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        return super(JSONField, self).get_db_prep_save(value)

try:
    from south.modelsinspector import add_introspection_rules
    from django.db.models.fields import NOT_PROVIDED
    from django.conf import settings

    JSONField_introspection_rule = (
            (JSONField,),
            [],
            {
            "null": ["null", {"default": False}],
            "blank": ["blank", {"default": False, "ignore_if":"primary_key"}],
            "primary_key": ["primary_key", {"default": False}],
            "max_length": ["max_length", {"default": None}],
            "unique": ["_unique", {"default": False}],
            "db_index": ["db_index", {"default": False}],
            "default": ["default", {"default": NOT_PROVIDED}],
            "db_column": ["db_column", {"default": None}],
            "db_tablespace": ["db_tablespace", {"default": settings.DEFAULT_INDEX_TABLESPACE}],
            },
    )

    add_introspection_rules(rules=[JSONField_introspection_rule], patterns=["^feincms\.contrib\.fields"])
except ImportError:
    pass
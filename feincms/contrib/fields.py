from __future__ import absolute_import, unicode_literals

import json
import logging
from distutils.version import LooseVersion

from django import get_version
from django import forms
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import six


class JSONFormField(forms.fields.CharField):
    def clean(self, value, *args, **kwargs):
        # It seems that sometimes we receive dict objects here, not only
        # strings. Partial form validation maybe?
        if value:
            if isinstance(value, six.string_types):
                try:
                    value = json.loads(value)
                except ValueError:
                    raise forms.ValidationError("Invalid JSON data!")

            try:
                # Run the value through JSON so we can normalize formatting
                # and at least learn about malformed data:
                value = json.dumps(value, cls=DjangoJSONEncoder)
            except ValueError:
                raise forms.ValidationError("Invalid JSON data!")

        return super(JSONFormField, self).clean(value, *args, **kwargs)


if LooseVersion(get_version()) > LooseVersion('1.8'):
    workaround_class = models.TextField
else:
    workaround_class = six.with_metaclass(
        models.SubfieldBase, models.TextField)


class JSONField(workaround_class):
    """
    TextField which transparently serializes/unserializes JSON objects

    See:
    http://www.djangosnippets.org/snippets/1478/
    """

    formfield = JSONFormField

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if isinstance(value, dict):
            return value
        elif (isinstance(value, six.string_types) or
                isinstance(value, six.binary_type)):
            # Avoid asking the JSON decoder to handle empty values:
            if not value:
                return {}

            try:
                return json.loads(value)
            except ValueError:
                logging.getLogger("feincms.contrib.fields").exception(
                    "Unable to deserialize store JSONField data: %s", value)
                return {}
        else:
            assert value is None
            return {}

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_prep_value(self, value):
        """Convert our JSON object to a string before we save"""
        return self._flatten_value(value)

    def value_to_string(self, obj):
        """Extract our value from the passed object and return it in string
        form"""

        if hasattr(obj, self.attname):
            value = getattr(obj, self.attname)
        else:
            assert isinstance(obj, dict)
            value = obj.get(self.attname, "")

        return self._flatten_value(value)

    def _flatten_value(self, value):
        """Return either a string, JSON-encoding dict()s as necessary"""
        if not value:
            return ""

        if isinstance(value, dict):
            value = json.dumps(value, cls=DjangoJSONEncoder)

        assert isinstance(value, six.string_types)

        return value

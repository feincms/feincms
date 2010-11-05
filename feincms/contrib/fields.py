import logging

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
            # Avoid asking the JSON decoder to handle empty values:
            if not value:
                return {}

            try:
                return json.loads(value)
            except ValueError:
                logging.getLogger("feincms.contrib.fields").exception("Unable to deserialize store JSONField data: %s", value)
                return {}
        else:
            assert value is None
            return {}

    def get_db_prep_value(self, value):
        """Convert our JSON object to a string before we save"""
        return self._flatten_value(value)

    def value_to_string(self, obj):
        """Extract our value from the passed object and return it in string form"""

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

        assert isinstance(value, basestring)

        return value

try:
    from south.modelsinspector import add_introspection_rules

    JSONField_introspection_rule = ( (JSONField,), [], {}, )

    add_introspection_rules(rules=[JSONField_introspection_rule], patterns=["^feincms\.contrib\.fields"])
except ImportError:
    pass

# taken from http://djangosnippets.org/snippets/2217/
# 17.10.2010
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import ManyToManyRawIdWidget, ForeignKeyRawIdWidget
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode
from django.utils.html import escape

class VerboseForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            change_url = reverse(
                "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.object_name.lower()),
                args=(obj.pk,)
            )
            return '&nbsp;<strong><a href="%s">%s</a></strong>' % (change_url, escape(obj))
        except (ValueError, self.rel.to.DoesNotExist):
            return ''

class VerboseManyToManyRawIdWidget(ManyToManyRawIdWidget):
    def label_for_value(self, value):
        values = value.split(',')
        str_values = ['<ul>',]
        key = self.rel.get_related_field().name
        for v in values:
            try:
                obj = self.rel.to._default_manager.using(self.db).get(**{key: v})
                x = smart_unicode(obj)
                change_url = reverse(
                    "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.object_name.lower()),
                    args=(obj.pk,)
                )
                str_values += ['<li><strong><a href="%s">%s</a></strong></li>' % (change_url, escape(x))]
            except self.rel.to.DoesNotExist:
                str_values += [u'???']
        
        str_values += ['</ul>',]
        return u' '.join(str_values)

class ImproveRawIdFieldsForm(admin.ModelAdmin):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs.pop("request", None)
            type = db_field.rel.__class__.__name__
            if type == "ManyToOneRel":
                kwargs['widget'] = VerboseForeignKeyRawIdWidget(db_field.rel)
            elif type == "ManyToManyRel":
                kwargs['widget'] = VerboseManyToManyRawIdWidget(db_field.rel)
            return db_field.formfield(**kwargs)
        return super(ImproveRawIdFieldsForm, self).formfield_for_dbfield(db_field, **kwargs)



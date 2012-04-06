from django import forms
from django.db import models


class RichTextFormField(forms.fields.CharField):
    def __init__(self, *args, **kwargs):
        super(RichTextFormField, self).__init__(*args, **kwargs)
        css_class = self.widget.attrs.get('class', '')
        css_class += ' item-richtext'
        self.widget.attrs['class'] = css_class

    def clean(self, value):
        # TODO add cleansing here?
        return super(RichTextFormField, self).clean(value)


class RichTextField(models.TextField):
    formfield = RichTextFormField


try:
    from south.modelsinspector import add_introspection_rules

    RichTextField_introspection_rule = ( (RichTextField,), [], {}, )

    add_introspection_rules(rules=[RichTextField_introspection_rule],
        patterns=["^feincms\.contrib\.richtext"])
except ImportError:
    pass

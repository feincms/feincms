from __future__ import absolute_import, unicode_literals

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
    """
    Drop-in replacement for Django's ``models.TextField`` which allows editing
    rich text instead of plain text in the item editor.
    """
    def formfield(self, form_class=RichTextFormField, **kwargs):
        return super(RichTextField, self).formfield(
            form_class=form_class, **kwargs)


try:
    from south.modelsinspector import add_introspection_rules

    RichTextField_introspection_rule = ((RichTextField,), [], {},)

    add_introspection_rules(
        rules=[RichTextField_introspection_rule],
        patterns=["^feincms\.contrib\.richtext"])
except ImportError:
    pass

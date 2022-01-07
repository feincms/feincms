from django import forms
from django.db import models


class RichTextFormField(forms.fields.CharField):
    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", None)
        super().__init__(*args, **kwargs)
        css_class = self.widget.attrs.get("class", "")
        css_class += " item-richtext"
        self.widget.attrs["class"] = css_class

    def clean(self, value):
        value = super().clean(value)
        if self.cleanse:
            value = self.cleanse(value)
        return value


class RichTextField(models.TextField):
    """
    Drop-in replacement for Django's ``models.TextField`` which allows editing
    rich text instead of plain text in the item editor.
    """

    def __init__(self, *args, **kwargs):
        self.cleanse = kwargs.pop("cleanse", None)
        super().__init__(*args, **kwargs)

    def formfield(self, form_class=RichTextFormField, **kwargs):
        return super().formfield(form_class=form_class, cleanse=self.cleanse, **kwargs)

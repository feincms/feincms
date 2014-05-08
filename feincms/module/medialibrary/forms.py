# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import os

from django import forms
from django.utils.translation import ugettext_lazy as _

from feincms import settings

from . import logger
from .models import Category, MediaFile
from .fields import AdminFileWithPreviewWidget


# ------------------------------------------------------------------------
class MediaCategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    def clean_parent(self):
        data = self.cleaned_data['parent']
        if data is not None and self.instance in data.path_list():
            raise forms.ValidationError(
                _("This would create a loop in the hierarchy"))

        return data

    def __init__(self, *args, **kwargs):
        super(MediaCategoryAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset =\
            self.fields['parent'].queryset.exclude(pk=self.instance.pk)


# ------------------------------------------------------------------------
class MediaFileAdminForm(forms.ModelForm):
    class Meta:
        model = MediaFile
        widgets = {'file': AdminFileWithPreviewWidget}
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(MediaFileAdminForm, self).__init__(*args, **kwargs)

        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            field = self.instance.file.field
            if not hasattr(field, '_feincms_generate_filename_patched'):
                original_generate = field.generate_filename

                def _gen_fname(instance, filename):
                    if instance.id and hasattr(instance, 'original_name'):
                        logger.info("Overwriting file %s with new data" % (
                            instance.original_name))
                        instance.file.storage.delete(instance.original_name)
                        return instance.original_name

                    return original_generate(instance, filename)

                field.generate_filename = _gen_fname
                field._feincms_generate_filename_patched = True

    def clean_file(self):
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            new_base, new_ext = os.path.splitext(
                self.cleaned_data['file'].name)
            old_base, old_ext = os.path.splitext(self.instance.file.name)

            if new_ext.lower() != old_ext.lower():
                raise forms.ValidationError(_(
                    "Cannot overwrite with different file type (attempt to"
                    " overwrite a %(old_ext)s with a %(new_ext)s)"
                ) % {'old_ext': old_ext, 'new_ext': new_ext})

            self.instance.original_name = self.instance.file.name

        return self.cleaned_data['file']

# ------------------------------------------------------------------------

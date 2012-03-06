# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

import os

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from . import logger
from .models import MediaFile

# ------------------------------------------------------------------------
class MediaFileAdminForm(forms.ModelForm):
    class Meta:
        model = MediaFile

    def __init__(self, *args, **kwargs):
        super(MediaFileAdminForm, self).__init__(*args, **kwargs)
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            self.original_name = self.instance.file.name

            def gen_fname(instance, filename):
                self.instance.file.storage.delete(self.original_name)
                return self.original_name
            self.instance.file.field.generate_filename = gen_fname

    def clean_file(self):
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and hasattr(self, 'original_name'):
            new_base, new_ext = os.path.splitext(self.cleaned_data['file'].name)
            old_base, old_ext = os.path.splitext(self.original_name)

            if new_ext.lower() != old_ext.lower():
                raise forms.ValidationError(_("Cannot overwrite with different file type (attempt to overwrite a %(old_ext)s with a %(new_ext)s)") % { 'old_ext': old_ext, 'new_ext': new_ext })

        return self.cleaned_data['file']

# ------------------------------------------------------------------------

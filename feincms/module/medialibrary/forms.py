# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

import os

from django import forms
from django.utils.translation import ugettext_lazy as _

from feincms import settings

from . import logger
from .models import MediaFile

# ------------------------------------------------------------------------
class MediaFileAdminForm(forms.ModelForm):
    class Meta:
        model = MediaFile

    def __init__(self, *args, **kwargs):
        super(MediaFileAdminForm, self).__init__(*args, **kwargs)
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            if not hasattr(self.instance.file.field, '_feincms_generate_filename_patched'):
                orig_generate_filename = self.instance.file.field.generate_filename

                def _gen_fname(instance, filename):
                    if instance.id and hasattr(instance, 'original_name'):
                        logger.info("Overwriting file %s with new data" % instance.original_name)
                        instance.file.storage.delete(instance.original_name)
                        return instance.original_name

                    return orig_generate_filename(instance, filename)

                self.instance.file.field.generate_filename = _gen_fname
                self.instance.file.field._feincms_generate_filename_patched = True

    def clean_file(self):
        if settings.FEINCMS_MEDIAFILE_OVERWRITE and self.instance.id:
            new_base, new_ext = os.path.splitext(self.cleaned_data['file'].name)
            old_base, old_ext = os.path.splitext(self.instance.file.name)

            if new_ext.lower() != old_ext.lower():
                raise forms.ValidationError(_("Cannot overwrite with different file type (attempt to overwrite a %(old_ext)s with a %(new_ext)s)") % { 'old_ext': old_ext, 'new_ext': new_ext })

            self.instance.original_name = self.instance.file.name

        return self.cleaned_data['file']

# ------------------------------------------------------------------------

"""
Simple file inclusion content: You should probably use the media library
instead.
"""

from __future__ import absolute_import, unicode_literals

import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms._internal import ct_render_to_string


class FileContent(models.Model):
    # You should probably use
    # `feincms.content.medialibrary.models.MediaFileContent` instead.

    title = models.CharField(max_length=200)
    file = models.FileField(
        _('file'), max_length=255,
        upload_to=os.path.join(settings.FEINCMS_UPLOAD_PREFIX, 'filecontent'))

    class Meta:
        abstract = True
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def render(self, **kwargs):
        return ct_render_to_string(
            [
                'content/file/%s.html' % self.region,
                'content/file/default.html',
            ],
            {'content': self},
            request=kwargs.get('request'),
            context=kwargs.get('context'),
        )

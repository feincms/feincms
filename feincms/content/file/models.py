"""
Simple file inclusion content: You should probably use the media library
instead.
"""

from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


class FileContent(models.Model):
    # You should probably use `feincms.content.medialibrary.models.MediaFileContent`
    # instead.

    title = models.CharField(max_length=200)
    file = models.FileField(_('file'), upload_to='filecontent')

    class Meta:
        abstract = True
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def render(self, **kwargs):
        return render_to_string([
            'content/file/%s.html' % self.region,
            'content/file/default.html',
            ], {'content': self})


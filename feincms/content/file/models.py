from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _


class FileContent(models.Model):
    title = models.CharField(max_length=200)
    file = models.FileField(_('file'), upload_to='filecontent')

    class Meta:
        abstract = True
        verbose_name = _('file')
        verbose_name_plural = _('files')

    def render(self, **kwargs):
        return render_to_string([
            'content/file/%s.html' % self.region.key,
            'content/file/default.html',
            ], {'content': self})


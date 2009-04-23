from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class RichTextContent(models.Model):
    text = models.TextField(_('text'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('rich text')
        verbose_name_plural = _('rich texts')

    def render(self, **kwargs):
        return mark_safe(self.text)


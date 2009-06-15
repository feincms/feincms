from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class RawContent(models.Model):
    text = models.TextField(_('content'), blank=True)

    class Meta:
        abstract = True
        verbose_name = _('raw content')
        verbose_name_plural = _('raw contents')

    def render(self, **kwargs):
        return mark_safe(self.text)


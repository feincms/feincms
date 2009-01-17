from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms.models import PageContent


class RichTextContent(PageContent):
    text = models.TextField(_('text'), blank=True)

    def render(self):
        return mark_safe(self.text)

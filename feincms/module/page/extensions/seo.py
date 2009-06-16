from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page


def register():
    Page.add_to_class('meta_keywords', models.TextField(_('meta keywords'), blank=True,
        help_text=_('This will be prepended to the default keyword list.')))
    Page.add_to_class('meta_description', models.TextField(_('meta description'), blank=True,
        help_text=_('This will be prepended to the default description.')))

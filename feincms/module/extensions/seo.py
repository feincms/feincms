"""
Add a keyword and a description field which are helpful for SEO optimization.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

def register(cls, admin_cls):
    cls.add_to_class('meta_keywords', models.TextField(_('meta keywords'), blank=True,
        help_text=_('This will be prepended to the default keyword list.')))
    cls.add_to_class('meta_description', models.TextField(_('meta description'), blank=True,
        help_text=_('This will be prepended to the default description.')))

    if admin_cls:
        admin_cls.search_fields.extend(['meta_keywords', 'meta_description'])

        admin_cls.add_extension_options(_('Search engine optimization'), {
            'fields': ('meta_keywords', 'meta_description'),
            'classes': ('collapse',),
            })

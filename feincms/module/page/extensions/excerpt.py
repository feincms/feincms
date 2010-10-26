"""
Add an excerpt field to the page.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

def register(cls, admin_cls):
    cls.add_to_class('excerpt', models.TextField(_('excerpt'), blank=True,
        help_text=_('Add a brief excerpt summarizing the content of this page.')))

    admin_cls.fieldsets.append((_('Excerpt'), {
        'fields': ('excerpt',),
        'classes': ('collapse',),
        }))

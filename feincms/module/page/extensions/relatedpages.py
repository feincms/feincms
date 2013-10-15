"""
Add a many-to-many relationship field to relate this page to other pages.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page


def register(cls, admin_cls):
    cls.add_to_class('related_pages', models.ManyToManyField(Page, blank=True,
        related_name='%(app_label)s_%(class)s_related',
        null=True, help_text=_('Select pages that should be listed as related content.')))

    admin_cls.filter_horizontal = list(getattr(admin_cls, 'filter_horizontal', ()))
    admin_cls.filter_horizontal.append('related_pages')

    admin_cls.add_extension_options(_('Related pages'), {
        'fields': ('related_pages',),
        'classes': ('collapse',),
        })

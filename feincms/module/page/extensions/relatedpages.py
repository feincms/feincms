"""
Add a many-to-many relatioship field to relate this page to other pages.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page

def register(cls, admin_cls):
    cls.add_to_class('related_pages', models.ManyToManyField(Page, blank=True,
        related_name='%(app_label)s_%(class)s_related',
        null=True, help_text=_('Select pages that should be listed as related content.')))

    try:
        admin_cls.filter_horizontal.append('related_pages')
    except AttributeError:
        admin_cls.filter_horizontal = ['related_pages']

    admin_cls.fieldsets.append((_('Related pages'), {
        'fields': ('related_pages',),
        'classes': ('collapse',),
        }))

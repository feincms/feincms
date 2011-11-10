"""
Add a "featured" field to objects so admins can better direct top content.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.admin import add_extension_options

def register(cls, admin_cls):
    cls.add_to_class('featured', models.BooleanField(_('featured')))

    if hasattr(cls, 'cache_key_components'):
        cls.cache_key_components.append(lambda page: page.featured)

    add_extension_options(admin_cls, _('Featured'), {
        'fields': ('featured',),
        })

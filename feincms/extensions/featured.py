"""
Add a "featured" field to objects so admins can better direct top content.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('featured', models.BooleanField(_('featured')))

        if hasattr(self.model, 'cache_key_components'):
            self.model.cache_key_components.append(lambda page: page.featured)

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options(_('Featured'), {
            'fields': ('featured',),
            'classes': ('collapse',),
        })

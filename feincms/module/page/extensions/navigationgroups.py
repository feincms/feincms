"""
Page navigation groups allow assigning pages to differing navigation lists
such as header, footer and what else.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    ident = 'navigationgroups'
    groups = [
        ('default', _('Default')),
        ('footer', _('Footer')),
    ]

    def handle_model(self):
        self.model.add_to_class(
            'navigation_group',
            models.CharField(
                _('navigation group'),
                choices=self.groups,
                default=self.groups[0][0],
                max_length=20,
                blank=True,
                db_index=True))

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options('navigation_group')
        modeladmin.extend_list('list_display', ['navigation_group'])
        modeladmin.extend_list('list_filter', ['navigation_group'])

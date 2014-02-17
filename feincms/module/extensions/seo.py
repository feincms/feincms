"""
Add a keyword and a description field which are helpful for SEO optimization.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('meta_keywords', models.TextField(
            _('meta keywords'),
            blank=True,
            help_text=_('Keywords are ignored by most search engines.')))
        self.model.add_to_class('meta_description', models.TextField(
            _('meta description'),
            blank=True,
            help_text=_('This text is displayed on the search results page. '
                        'It is however not used for the SEO ranking. '
                        'Text longer than 140 characters is truncated.')))

    def handle_modeladmin(self, modeladmin):
        modeladmin.extend_list(
            'search_fields',
            ['meta_keywords', 'meta_description'],
        )

        modeladmin.add_extension_options(_('Search engine optimization'), {
            'fields': ('meta_keywords', 'meta_description'),
            'classes': ('collapse',),
        })

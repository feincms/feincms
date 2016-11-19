"""
This introduces a new page type, which has no content of its own but inherits
all content from the linked page.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms._internal import monkeypatch_property


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('symlinked_page', models.ForeignKey(
            'self',
            blank=True,
            null=True,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_symlinks',
            verbose_name=_('symlinked page'),
            help_text=_('All content is inherited from this page if given.')))

        @monkeypatch_property(self.model)
        def content(self):
            if not hasattr(self, '_content_proxy'):
                if self.symlinked_page:
                    self._content_proxy = self.content_proxy_class(
                        self.symlinked_page)
                else:
                    self._content_proxy = self.content_proxy_class(self)

            return self._content_proxy

    def handle_modeladmin(self, modeladmin):
        modeladmin.extend_list('raw_id_fields', ['symlinked_page'])
        modeladmin.add_extension_options('symlinked_page')

"""
Simple tagging support using ``django-tagging``.
"""

from __future__ import absolute_import, unicode_literals

from django.utils.translation import ugettext_lazy as _

from feincms import extensions

import tagging
from tagging.fields import TagField


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('tags', TagField(_('tags')))

        # use another name for the tag descriptor See
        # http://code.google.com/p/django-tagging/issues/detail?id=95 for the
        # reason why
        tagging.register(self.model, tag_descriptor_attr='etags')

    def handle_modeladmin(self, modeladmin):
        modeladmin.add_extension_options('tags')

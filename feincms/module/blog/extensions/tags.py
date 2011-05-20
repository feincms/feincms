"""
Simple tagging support using ``django-tagging``.
"""

from django.utils.translation import ugettext_lazy as _

import tagging
from tagging.fields import TagField


def register(cls, admin_cls):
    cls.add_to_class('tags', TagField(_('tags')))

    # use another name for the tag descriptor
    # See http://code.google.com/p/django-tagging/issues/detail?id=95 for the reason why
    tagging.register(cls, tag_descriptor_attr='etags')

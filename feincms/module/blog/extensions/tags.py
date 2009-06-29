from django.utils.translation import ugettext_lazy as _

from feincms.module.blog.models import Entry

import tagging
from tagging.fields import TagField


def register():
    Entry.add_to_class('tags', TagField(_('tags')))

    # use another name for the tag descriptor
    # See http://code.google.com/p/django-tagging/issues/detail?id=95 for the reason why
    tagging.register(Entry, tag_descriptor_attr='etags')

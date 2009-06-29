from django.utils.translation import ugettext_lazy as _

from feincms.module.blog.models import Entry

import tagging
from tagging.fields import TagField


def register():
    Entry.add_to_class('tags', TagField(_('tags')))

    tagging.register(Entry, tag_descriptor_attr='etags')

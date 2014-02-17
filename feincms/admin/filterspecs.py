# encoding=utf-8
# Thanks to http://www.djangosnippets.org/snippets/1051/
#
# Authors: Marinho Brandao <marinho at gmail.com>
#          Guilherme M. Gondim (semente) <semente at taurinus.org>

from __future__ import absolute_import, unicode_literals

from django.contrib.admin.filters import (
    FieldListFilter, ChoicesFieldListFilter)
from django.utils import six
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from feincms.utils import shorten_string


class ParentFieldListFilter(ChoicesFieldListFilter):
    """
    Improved list_filter display for parent Pages by nicely indenting hierarchy

    In theory this would work with any mptt model which uses a "title"
    attribute.

    my_model_field.page_parent_filter = True
    """

    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(ParentFieldListFilter, self).__init__(
            f, request, params, model, model_admin, field_path)

        parent_ids = model.objects.exclude(parent=None).values_list(
            "parent__id", flat=True).order_by("parent__id").distinct()
        parents = model.objects.filter(pk__in=parent_ids).values_list(
            "pk", "title", "level")
        self.lookup_choices = [(
            pk,
            "%s%s" % ("&nbsp;" * level, shorten_string(title, max_length=25)),
        ) for pk, title, level in parents]

    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }

        for pk, title in self.lookup_choices:
            yield {
                'selected': pk == int(self.lookup_val or '0'),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display': mark_safe(smart_text(title))
            }

    def title(self):
        return _('Parent')


class CategoryFieldListFilter(ChoicesFieldListFilter):
    """
    Customization of ChoicesFilterSpec which sorts in the user-expected format

    my_model_field.category_filter = True
    """

    def __init__(self, f, request, params, model, model_admin,
                 field_path=None):
        super(CategoryFieldListFilter, self).__init__(
            f, request, params, model, model_admin, field_path)

        # Restrict results to categories which are actually in use:
        self.lookup_choices = [(
            i.pk,
            six.text_type(i))
            for i in f.related.parent_model.objects.exclude(
                **{f.related.var_name: None})
        ]
        self.lookup_choices.sort(key=lambda i: i[1])

    def choices(self, cl):
        yield {
            'selected': self.lookup_val is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All')
        }

        for pk, title in self.lookup_choices:
            yield {
                'selected': pk == int(self.lookup_val or '0'),
                'query_string': cl.get_query_string({self.lookup_kwarg: pk}),
                'display': mark_safe(smart_text(title))
            }

    def title(self):
        return _('Category')


FieldListFilter.register(
    lambda f: getattr(f, 'parent_filter', False),
    ParentFieldListFilter,
    take_priority=True)
FieldListFilter.register(
    lambda f: getattr(f, 'category_filter', False),
    CategoryFieldListFilter,
    take_priority=True)

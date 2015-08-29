# encoding=utf-8
# Thanks to http://www.djangosnippets.org/snippets/1051/
#
# Authors: Marinho Brandao <marinho at gmail.com>
#          Guilherme M. Gondim (semente) <semente at taurinus.org>

from __future__ import absolute_import, unicode_literals

from django.contrib.admin.filters import ChoicesFieldListFilter
from django.db.models import Count
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django import VERSION as DJANGO_VERSION

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
            "%s%s" % (
                "&nbsp;&nbsp;" * level,
                shorten_string(title, max_length=25)),
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
        if DJANGO_VERSION < (1, 8):
            related_model = f.related.parent_model
            related_name = f.related.var_name
        else:
            related_model = f.rel.to
            related_name = f.related_query_name()

        self.lookup_choices = sorted(
            [
                (i.pk, '%s (%s)' % (i, i._related_count))
                for i in related_model.objects.annotate(
                    _related_count=Count(related_name)
                ).exclude(_related_count=0)
            ],
            key=lambda i: i[1],
        )

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

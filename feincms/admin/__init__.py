from __future__ import absolute_import

from django.contrib.admin.filters import FieldListFilter
from .filters import ParentFieldListFilter, CategoryFieldListFilter


FieldListFilter.register(
    lambda f: getattr(f, 'parent_filter', False),
    ParentFieldListFilter,
    take_priority=True)
FieldListFilter.register(
    lambda f: getattr(f, 'category_filter', False),
    CategoryFieldListFilter,
    take_priority=True)

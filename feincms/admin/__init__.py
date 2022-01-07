from django.contrib.admin.filters import FieldListFilter

from .filters import CategoryFieldListFilter, ParentFieldListFilter


FieldListFilter.register(
    lambda f: getattr(f, "parent_filter", False),
    ParentFieldListFilter,
    take_priority=True,
)
FieldListFilter.register(
    lambda f: getattr(f, "category_filter", False),
    CategoryFieldListFilter,
    take_priority=True,
)

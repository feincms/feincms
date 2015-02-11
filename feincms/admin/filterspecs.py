from __future__ import absolute_import, unicode_literals

import warnings

from .filters import ParentFieldListFilter, CategoryFieldListFilter

__all__ = ('ParentFieldListFilter', 'CategoryFieldListFilter')

warnings.warn(
    'feincms.admin.filterspecs has been renamed to feincms.admin.filters.',
    DeprecationWarning, stacklevel=2)

from __future__ import absolute_import

import warnings

from feincms.templatetags.feincms_page_tags import (
    feincms_nav, feincms_translated_or_base, feincms_breadcrumbs,
    is_equal_or_parent_of, is_sibling_of, siblings_along_path_to,
    page_is_active)

__all__ = (
    'feincms_nav', 'feincms_translated_or_base', 'feincms_breadcrumbs',
    'is_equal_or_parent_of', 'is_sibling_of', 'siblings_along_path_to',
    'page_is_active',
)

warnings.warn(
    'feincms_page_tags has been moved to'
    ' feincms.templatetags.feincms_page_tags.',
    DeprecationWarning, stacklevel=2)

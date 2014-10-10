"""
Third-party application inclusion support.
"""

from __future__ import absolute_import, unicode_literals

import warnings

warnings.warn(
    'Import application content code from feincms.apps instead.',
    DeprecationWarning, stacklevel=2)


__all__ = (
    'ApplicationContent', 'app_reverse', 'app_reverse_lazy', 'permalink',
    'UnpackTemplateResponse',
)


from feincms.apps import (
    ApplicationContent, app_reverse, app_reverse_lazy, permalink,
    UnpackTemplateResponse,
)

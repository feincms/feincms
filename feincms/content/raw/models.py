from __future__ import absolute_import, unicode_literals

import warnings
warnings.warn(
    'Import RawContent from feincms.contents instead.',
    DeprecationWarning, stacklevel=2)

__all__ = ('RawContent',)

from feincms.contents import RawContent

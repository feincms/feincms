from __future__ import absolute_import

import warnings

from feincms.applications import standalone, unpack

__all__ = ('standalone', 'unpack')


warnings.warn(
    'Import @standalone and @unpack from feincms.applications.',
    DeprecationWarning, stacklevel=2)

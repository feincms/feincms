from __future__ import absolute_import, unicode_literals

import warnings
warnings.warn(
    'Import @standalone and @unpack from feincms.apps.',
    DeprecationWarning, stacklevel=2)

from feincms.apps import standalone, unpack
__all__ = ('standalone', 'unpack')

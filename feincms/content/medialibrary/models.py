# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import warnings
warnings.warn(
    'Import MediaFileContent from feincms.contents instead.',
    DeprecationWarning, stacklevel=2)

__all__ = ('MediaFileContent',)

from feincms.contents import MediaFileContent

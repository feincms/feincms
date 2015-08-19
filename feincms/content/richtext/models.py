from __future__ import absolute_import, unicode_literals

import warnings
warnings.warn(
    'Import RichTextContent from feincms.contents instead.',
    DeprecationWarning, stacklevel=2)

__all__ = ('RichTextContent',)

from feincms.contents import RichTextContent

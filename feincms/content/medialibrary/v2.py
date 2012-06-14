from __future__ import absolute_import
import warnings


warnings.warn(
    'The contents of feincms.content.medialibrary.v2 have been moved to'
    ' feincms.content.medialibrary.models. Support for importing those'
    ' classes through v2 will be removed in FeinCMS v1.8.',
    DeprecationWarning, stacklevel=2)


from .models import *

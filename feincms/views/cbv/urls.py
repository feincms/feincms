from __future__ import absolute_import

import warnings

from feincms.urls import urlpatterns, Handler, handler

__all__ = ('urlpatterns', 'Handler', 'handler')

warnings.warn(
    'feincms.views.cbv has been deprecated. Use feincms.urls and feincms.views'
    ' directly instead.', DeprecationWarning, stacklevel=2)

# flake8: noqa
from __future__ import absolute_import, unicode_literals

import warnings

from feincms.extensions.translations import *

warnings.warn(
    'Import %(name)s from feincms.extensions.%(name)s' % {
        'name': __name__.split('.')[-1],
    }, DeprecationWarning, stacklevel=2)

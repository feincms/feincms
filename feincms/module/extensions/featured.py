# flake8: noqa
from __future__ import absolute_import, unicode_literals

import warnings

from feincms.extensions.featured import *

warnings.warn(
    'Import %s from feincms.extensions.%s' % (__name__, __name__),
    DeprecationWarning, stacklevel=2)

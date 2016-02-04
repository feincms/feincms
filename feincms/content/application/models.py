# flake8: noqa
from __future__ import absolute_import, unicode_literals

import warnings

from feincms.apps import *

warnings.warn(
    'Import ApplicationContent and friends from feincms.apps.',
    DeprecationWarning, stacklevel=2)


def cycle_app_reverse_cache(*args, **kwargs):
    warnings.warn(
        'cycle_app_reverse_cache does nothing and will be removed in'
        ' a future version of FeinCMS.',
        DeprecationWarning, stacklevel=2,
    )

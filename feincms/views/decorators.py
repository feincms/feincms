# flake8: noqa
from __future__ import absolute_import, unicode_literals

import warnings

from feincms.apps import *

warnings.warn(
    'Import ApplicationContent and friends from feincms.apps.',
    DeprecationWarning, stacklevel=2)

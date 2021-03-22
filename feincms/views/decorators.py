# flake8: noqa
from __future__ import absolute_import, unicode_literals

import warnings

from feincms.content.application.models import *


warnings.warn(
    "Import ApplicationContent and friends from feincms.content.application.models",
    DeprecationWarning,
    stacklevel=2,
)

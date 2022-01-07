# flake8: noqa

import warnings


warnings.warn(
    "Import ApplicationContent and friends from feincms.content.application.models",
    DeprecationWarning,
    stacklevel=2,
)

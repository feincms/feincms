# flake8: noqa

import warnings


warnings.warn(
    "Import %(name)s from feincms.extensions.%(name)s"
    % {"name": __name__.split(".")[-1]},
    DeprecationWarning,
    stacklevel=2,
)

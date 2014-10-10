import warnings

from feincms.extensions.datepublisher import (
    Extension, format_date, granular_now)

warnings.warn(
    'Import datepublisher from feincms.extensions.datepublisher.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension', 'format_date', 'granular_now')

import warnings
warnings.warn(
    'Import changedate from feincms.extensions.changedate.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension',)
from feincms.extensions.changedate import Extension

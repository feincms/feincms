import warnings
warnings.warn(
    'Import featured from feincms.extensions.featured.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension',)
from feincms.extensions.featured import Extension

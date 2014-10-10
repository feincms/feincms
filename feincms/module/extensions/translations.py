import warnings

from feincms.extensions.translations import Extension

warnings.warn(
    'Import translations from feincms.extensions.translations.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension',)

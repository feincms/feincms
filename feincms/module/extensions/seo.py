import warnings
warnings.warn(
    'Import seo from feincms.extensions.seo.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension',)
from feincms.extensions.seo import Extension

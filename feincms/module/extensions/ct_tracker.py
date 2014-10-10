import warnings
warnings.warn(
    'Import ct_tracker from feincms.extensions.ct_tracker.',
    DeprecationWarning, stacklevel=2)

__all__ = ('Extension', 'TrackerContentProxy')
from feincms.extensions.ct_tracker import Extension, TrackerContentProxy

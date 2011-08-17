import warnings
warnings.warn('feincms.views.base is deprecated. Please use feincms.views.legacy if '
    'you want to keep on using the old handler. Otherwise, it is advised to switch '
    'to the class-based view (Django >= 1.3 only).',
    DeprecationWarning, stacklevel=2)

from feincms.views.legacy.views import *

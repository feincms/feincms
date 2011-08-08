import warnings
warnings.warning('feincms.views.base is deprecated. Please use feincms.views.legacy if '
    'you want to keep on using the old handler. Otherwise, it is advised to switch '
    'to the class-based view (Django >= 1.3 only).',
    DeprecationWarning)

from feincms.views.legacy.views import *

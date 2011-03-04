VERSION = (1, 3, 0, 'pre')
__version__ = '.'.join(map(str, VERSION))


# Do not use Django settings at module level as recommended
from django.utils.functional import LazyObject

class LazySettings(LazyObject):
    def _setup(self):
        from feincms import default_settings
        self._wrapped = Settings(default_settings)

class Settings(object):
    def __init__(self, settings_module):
        for setting in dir(settings_module):
            if setting == setting.upper():
                setattr(self, setting, getattr(settings_module, setting))

settings = LazySettings()

COMPLETELY_LOADED = False
def ensure_completely_loaded():
    """
    This method ensures all models are completely loaded

    FeinCMS requires Django to be completely initialized before proceeding,
    because of the extension mechanism and the dynamically created content
    types.

    For more informations, have a look at issue #23 on github:
    http://github.com/matthiask/feincms/issues#issue/23
    """

    global COMPLETELY_LOADED
    if COMPLETELY_LOADED:
        return True

    from django.core.management.validation import get_validation_errors
    from StringIO import StringIO
    get_validation_errors(StringIO(), None)

    COMPLETELY_LOADED = True
    return True

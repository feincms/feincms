VERSION = (1, 1, 4)
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
    global COMPLETELY_LOADED
    if COMPLETELY_LOADED:
        return

    # Make sure all models are completely loaded before attempting to
    # proceed. The dynamic nature of FeinCMS models makes this necessary.
    # For more informations, have a look at issue #23 on github:
    # http://github.com/matthiask/feincms/issues#issue/23
    from django.core.management.validation import get_validation_errors
    from StringIO import StringIO
    get_validation_errors(StringIO(), None)

    COMPLETELY_LOADED = True

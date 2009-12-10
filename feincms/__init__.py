VERSION = (1, 0, 4)
__version__ = '.'.join(map(str, VERSION))


# Do not use Django settings at module level as recommended
from django.utils.functional import LazyObject
from feincms import default_settings

class LazySettings(LazyObject):
    def _setup(self):
        self._wrapped = Settings(default_settings)

class Settings(object):
    def __init__(self, settings_module):
        for setting in dir(settings_module):
            if setting == setting.upper():
                setattr(self, setting, getattr(settings_module, setting))

settings = LazySettings()

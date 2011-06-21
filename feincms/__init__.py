VERSION = (1, 4, 0, 'pre')
__version__ = '.'.join(map(str, VERSION))


class LazySettings(object):
    def _load_settings(self):
        from feincms import default_settings
        from django.conf import settings as django_settings

        for key in dir(default_settings):
            if not key.startswith('FEINCMS_'):
                continue

            setattr(self, key, getattr(django_settings, key,
                getattr(default_settings, key)))

    def __getattr__(self, attr):
        self._load_settings()
        del self.__class__.__getattr__
        return self.__dict__[attr]

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

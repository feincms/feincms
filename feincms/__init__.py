VERSION = (1, 5, 0, 'rc1')
__version__ = '.'.join(map(str, VERSION))


class LazySettings(object):
    def _load_settings(self):
        from feincms import default_settings
        from django.conf import settings as django_settings

        for key in dir(default_settings):
            if not (key.startswith('FEINCMS_') or key.startswith('_HACK_')):
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
    http://github.com/feincms/feincms/issues#issue/23
    """

    global COMPLETELY_LOADED
    if COMPLETELY_LOADED:
        return True

    # Ensure meta information concerning related fields is up-to-date.
    # Upon accessing the related fields information from Model._meta,
    # the related fields are cached and never refreshed again (because
    # models and model relations are defined upon import time, if you
    # do not fumble around with models like we do in FeinCMS.)
    #
    # Here we flush the caches rather than actually _filling them so
    # that relations defined after all content types registrations
    # don't miss out.
    from django.db.models import loading
    for model in loading.get_models():
        for cache_name in ('_field_cache', '_field_name_cache', '_m2m_cache',
                '_related_objects_cache', '_related_many_to_many_cache',
                '_name_map'):
            try:
                delattr(model._meta, cache_name)
            except AttributeError:
                pass

    COMPLETELY_LOADED = True
    return True

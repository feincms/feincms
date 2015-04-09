from __future__ import absolute_import, unicode_literals

VERSION = (1, 11, 0, 'pre')
__version__ = '.'.join(map(str, VERSION))


class LazySettings(object):
    def _load_settings(self):
        from feincms import default_settings
        from django.conf import settings as django_settings

        for key in dir(default_settings):
            if not key.startswith('FEINCMS_'):
                continue

            value = getattr(default_settings, key)
            value = getattr(django_settings, key, value)
            setattr(self, key, value)

    def __getattr__(self, attr):
        self._load_settings()
        del self.__class__.__getattr__
        return self.__dict__[attr]

settings = LazySettings()


COMPLETELY_LOADED = False


def ensure_completely_loaded(force=False):
    """
    This method ensures all models are completely loaded

    FeinCMS requires Django to be completely initialized before proceeding,
    because of the extension mechanism and the dynamically created content
    types.

    For more informations, have a look at issue #23 on github:
    http://github.com/feincms/feincms/issues#issue/23
    """

    global COMPLETELY_LOADED
    if COMPLETELY_LOADED and not force:
        return True

    try:
        from django.apps import apps
    except ImportError:
        from django.db.models import loading as apps
    else:
        # Django 1.7 and up
        if not apps.ready:
            return

    # Ensure meta information concerning related fields is up-to-date.
    # Upon accessing the related fields information from Model._meta,
    # the related fields are cached and never refreshed again (because
    # models and model relations are defined upon import time, if you
    # do not fumble around with models like we do in FeinCMS.)
    #
    # Here we flush the caches rather than actually _filling them so
    # that relations defined after all content types registrations
    # don't miss out.
    import django
    if django.get_version() < '1.8':

        from feincms._internal import get_models
        for model in get_models():
            for cache_name in (
                    '_field_cache', '_field_name_cache', '_m2m_cache',
                    '_related_objects_cache', '_related_many_to_many_cache',
                    '_name_map'):
                try:
                    delattr(model._meta, cache_name)
                except AttributeError:
                    pass

            # Randomly call some cache filling methods
            # http://goo.gl/XNI2qz
            model._meta._fill_fields_cache()

        # Calls to get_models(...) are cached by the arguments used in the call.
        # This cache is normally cleared in loading.register_models(), but we
        # invalidate the get_models() cache, by calling get_models
        # above before all apps have loaded. (Django's load_app() doesn't clear the
        # get_models cache as it perhaps should). So instead we clear the
        # get_models cache again here. If we don't do this, Django 1.5 chokes on
        # a model validation error (Django 1.4 doesn't exhibit this problem).
        # See Issue #323 on github.
        if hasattr(apps, 'cache'):
            try:
                apps.cache.get_models.cache_clear()  # Django 1.7+
            except AttributeError:
                apps.cache._get_models_cache.clear()  # Django 1.6-

    if hasattr(apps, 'ready'):
        if apps.ready:
            COMPLETELY_LOADED = True
    elif apps.app_cache_ready():
            COMPLETELY_LOADED = True

    return True

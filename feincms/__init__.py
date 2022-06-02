VERSION = (22, 4, 0)
__version__ = ".".join(map(str, VERSION))


class LazySettings:
    def _load_settings(self):
        from django.conf import settings as django_settings

        from feincms import default_settings

        for key in dir(default_settings):
            if not key.startswith("FEINCMS_"):
                continue

            value = getattr(default_settings, key)
            value = getattr(django_settings, key, value)
            setattr(self, key, value)

    def __getattr__(self, attr):
        self._load_settings()
        del self.__class__.__getattr__
        return self.__dict__[attr]


settings = LazySettings()

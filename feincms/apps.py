def __getattr__(key):
    # Work around Django 3.2's autoloading of *.apps modules (AppConfig
    # autodiscovery)
    if key in {
        "ApplicationContent",
        "app_reverse",
        "app_reverse_lazy",
        "permalink",
        "UnpackTemplateResponse",
        "standalone",
        "unpack",
    }:
        from feincms.content.application import models

        return getattr(models, key)

    raise AttributeError("Unknown attribute '%s'" % key)

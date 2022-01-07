# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured

from feincms import settings

from .modeladmins import PageAdmin
from .models import Page


# ------------------------------------------------------------------------

if settings.FEINCMS_USE_PAGE_ADMIN:
    try:
        Page._meta.get_field("template_key")
    except FieldDoesNotExist:
        raise ImproperlyConfigured(
            "The page module requires a 'Page.register_templates()' call "
            "somewhere ('Page.register_regions()' is not sufficient). "
            "If you're not using the default Page admin, maybe try "
            "FEINCMS_USE_PAGE_ADMIN=False to avoid this warning."
        )

    admin.site.register(Page, PageAdmin)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

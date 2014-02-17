# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import FieldDoesNotExist

from feincms import ensure_completely_loaded, settings
from .models import Page
from .modeladmins import PageAdmin

# ------------------------------------------------------------------------

if settings.FEINCMS_USE_PAGE_ADMIN:
    ensure_completely_loaded()
    try:
        Page._meta.get_field('template_key')
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

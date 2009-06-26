from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured

from feincms.module.page.models import Page, PageAdmin


if not hasattr(Page, 'template'):
    raise ImproperlyConfigured, 'You need to register at least one template for Page before the admin code is included.'

admin.site.register(Page, PageAdmin)

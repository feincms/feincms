from django.contrib import admin

from feincms.module.page.models import Page, PageAdmin


admin.site.register(Page, PageAdmin)

from django.contrib import admin

from feincms.module.page.models import Page, PageAdmin


Page._needs_templates()
admin.site.register(Page, PageAdmin)

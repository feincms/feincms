from django.contrib import admin

from feincms.admin import PageAdmin
from feincms.content.image import models
from feincms.models import Page


class ImageContentInline(admin.StackedInline):
    model = models.ImageContent
    extra = 1


PageAdmin.inlines.append(ImageContentInline)

admin.site.unregister(Page)
admin.site.register(Page, PageAdmin)


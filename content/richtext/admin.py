from django.contrib import admin

from feincms.admin import PageAdmin
from feincms.content.richtext import models
from feincms.models import Page


class RichTextContentInline(admin.StackedInline):
    model = models.RichTextContent
    extra = 1


PageAdmin.inlines.append(RichTextContentInline)

admin.site.unregister(Page)
admin.site.register(Page, PageAdmin)


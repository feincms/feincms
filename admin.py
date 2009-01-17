from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from feincms import models

class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('active', 'template', 'title', 'parent'),
        }),
        (_('Content'), {
            #'classes': ('collapse',),
            'fields': ('_content_title',),
        }),
        (_('Language settings'), {
            #'classes': ('collapse',),
            'fields': ('language', 'translations'),
        }),
        (_('Other options'), {
            'classes': ('collapse',),
            'fields': ('slug', 'in_navigation', '_page_title', 'override_url', 'meta_keywords', 'meta_description'),
        }),
        )
    list_display=('__unicode__', 'title', 'active', 'in_navigation', 'language', 'template')
    list_filter=('active', 'in_navigation', 'language', 'template')
    prepopulated_fields={
        'slug': ('title',),
        }
    inlines = []

admin.site.register(models.Region,
    list_display=('key', 'inherited'),
    )
admin.site.register(models.Template,
    list_display=('title', 'path'),
    )
admin.site.register(models.Page, PageAdmin)


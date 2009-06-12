from django.contrib import admin

from feincms.module.medialibrary import models


class MediaFileTranslationInline(admin.TabularInline):
    model = models.MediaFileTranslation


admin.site.register(models.Category)
admin.site.register(models.MediaFile,
    date_hierarchy='created',
    inlines=[MediaFileTranslationInline],
    list_display=('__unicode__', 'copyright', 'created'),
    list_filter=('categories',),
    search_fields=('copyright', 'file', 'translations__caption',),
    )


from django.contrib import admin
from django.conf import settings

from feincms.module.medialibrary import models


class MediaFileTranslationInline(admin.StackedInline):
    model = models.MediaFileTranslation
    max_num = len(settings.LANGUAGES)

admin.site.register(models.Category)
admin.site.register(models.MediaFile,
    date_hierarchy='created',
    inlines=[MediaFileTranslationInline],
    list_display=('__unicode__', 'file_type', 'copyright', 'file_info', 'file_size', 'created'),
    list_filter=('categories', 'type'),
    search_fields=('copyright', 'file', 'translations__caption',),
    )


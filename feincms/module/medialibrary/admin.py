from django.contrib import admin

from feincms.module.medialibrary.models import Category, CategoryAdmin, MediaFile, MediaFileAdmin

admin.site.register(Category, CategoryAdmin)
admin.site.register(MediaFile, MediaFileAdmin)
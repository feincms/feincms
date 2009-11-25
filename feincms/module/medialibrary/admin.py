from django.contrib import admin

from feincms.module.medialibrary.models import Category, MediaFile, MediaFileAdmin

admin.site.register(Category)
admin.site.register(MediaFile, MediaFileAdmin)
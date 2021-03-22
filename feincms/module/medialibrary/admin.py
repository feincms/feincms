# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .modeladmins import CategoryAdmin, MediaFileAdmin
from .models import Category, MediaFile


# ------------------------------------------------------------------------
admin.site.register(Category, CategoryAdmin)
admin.site.register(MediaFile, MediaFileAdmin)

# ------------------------------------------------------------------------

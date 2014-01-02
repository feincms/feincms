# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import Category, MediaFile
from .modeladmins import CategoryAdmin, MediaFileAdmin

# ------------------------------------------------------------------------
admin.site.register(Category, CategoryAdmin)
admin.site.register(MediaFile, MediaFileAdmin)

# ------------------------------------------------------------------------

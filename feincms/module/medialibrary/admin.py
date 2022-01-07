# ------------------------------------------------------------------------
# ------------------------------------------------------------------------


from django.contrib import admin

from .modeladmins import CategoryAdmin, MediaFileAdmin
from .models import Category, MediaFile


# ------------------------------------------------------------------------
admin.site.register(Category, CategoryAdmin)
admin.site.register(MediaFile, MediaFileAdmin)

# ------------------------------------------------------------------------

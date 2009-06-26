from django.contrib import admin

from feincms.module.blog.models import Entry, EntryAdmin


admin.site.register(Entry, EntryAdmin)

from django.contrib import admin

from feincms.admin import tree_editor

from example.models import Category


class CategoryAdmin(tree_editor.TreeEditor):
    list_display = ('name', 'slug')
    list_filter = ('parent',)
    prepopulated_fields = {
        'slug': ('name',),
    }

admin.site.register(Category, CategoryAdmin)

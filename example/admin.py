from django.contrib import admin

from example.models import Category


admin.site.register(Category,
    list_display=('name', 'slug'),
    prepopulated_fields={
        'slug': ('name',),
        },
    )

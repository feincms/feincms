from django.contrib import admin

from feincms.models import Region, Template


admin.site.register(Region,
    list_display=('title', 'key', 'inherited'),
    )
admin.site.register(Template,
    list_display=('title', 'path'),
    )


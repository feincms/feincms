from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _


from feincms.admin import editor
from feincms.module.page.models import Page


if not hasattr(Page, 'template'):
    raise ImproperlyConfigured, 'You need to register at least one template for Page before the admin code is includede'


class PageAdmin(editor.ItemEditorMixin, editor.TreeEditorMixin, admin.ModelAdmin):
    # the fieldsets config here is used for the add_view, it has no effect
    # for the change_view which is completely customized anyway
    fieldsets = (
        (None, {
            'fields': ('active', 'in_navigation', 'template_key', 'title', 'slug',
                'parent'),
        }),
        (_('Other options'), {
            'classes': ('collapse',),
            'fields': ('override_url',),
        }),
        )
    list_display=('__unicode__', '_cached_url', 'active', 'in_navigation',
        'template')
    list_filter=('active', 'in_navigation', 'template_key')
    search_fields = ('title', 'slug', '_content_title', '_page_title',
        'meta_keywords', 'meta_description')
    prepopulated_fields={
        'slug': ('title',),
        }

    show_on_top = ('title', 'active', 'in_navigation')

admin.site.register(Page, PageAdmin)

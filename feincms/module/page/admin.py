from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


from feincms.admin import editor
from feincms.module.page.models import Page


class PageAdmin(editor.ItemEditorMixin, editor.TreeEditorMixin, admin.ModelAdmin):
    # the fieldsets config here is used for the add_view, it has no effect
    # for the change_view which is completely customized anyway
    fieldsets = (
        (None, {
            'fields': ('active', 'in_navigation', 'template', 'title', 'slug',
                'parent', 'language'),
        }),
        (_('Other options'), {
            'classes': ('collapse',),
            'fields': ('override_url', 'meta_keywords', 'meta_description'),
        }),
        )
    list_display=('__unicode__', 'active', 'in_navigation',
        'language', 'template')
    list_filter=('active', 'in_navigation', 'language', 'template')
    search_fields = ('title', 'slug', '_content_title', '_page_title',
        'meta_keywords', 'meta_description')
    prepopulated_fields={
        'slug': ('title',),
        }

    show_on_top = ('title', 'active', 'in_navigation')

admin.site.register(Page, PageAdmin)

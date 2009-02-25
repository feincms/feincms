import re

from django import forms, template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.core import serializers
from django.db import connection, transaction
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext_lazy as _

from feincms.models import Region, Template, Page, PageContent

from feincms.admin import editor


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

    content_model = PageContent


admin.site.register(Region,
    list_display=('title', 'key', 'inherited'),
    )
admin.site.register(Template,
    list_display=('title', 'path'),
    )
admin.site.register(Page, PageAdmin)

from django import forms, template
from django.contrib import admin
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.util import unquote, flatten_fieldsets
from django.forms.models import modelform_factory, inlineformset_factory
from django.contrib.admin import helpers
from django.db import models, transaction
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from django.forms.formsets import all_valid
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
import re


from feincms.models import Region, Template, PageManager, Page, PageContent
from projects.models import Project
from feincms.content.richtext.models import RichTextContent

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project

class PageForm(forms.ModelForm):
    class Meta:
        model = Page

class RichTextContentForm(forms.ModelForm):
    class Meta:
        model = RichTextContent

class PageAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('active', 'template', 'title', 'parent'),
        }),
        (_('Content'), {
            #'classes': ('collapse',),
            'fields': ('_content_title',),
        }),
        (_('Language settings'), {
            #'classes': ('collapse',),
            'fields': ('language', 'translations'),
        }),
        (_('Other options'), {
            'classes': ('collapse',),
            'fields': ('slug', 'in_navigation', '_page_title', 'override_url', 'meta_keywords', 'meta_description'),
        }),
        )
    list_display=('__unicode__', 'title', 'active', 'in_navigation', 'language', 'template')
    list_filter=('active', 'in_navigation', 'language', 'template')
    search_fields = ('title', '_content_title')
    prepopulated_fields={
        'slug': ('title',),
        }
    inlines = []

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.admin_site.name, self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns('',
            url(r'^$',
                wrap(self.changelist_view),
                name='%sadmin_%s_%s_changelist' % info),
            url(r'^add/$',
                wrap(self.add_view),
                name='%sadmin_%s_%s_add' % info),
            url(r'^(.+)/history/$',
                wrap(self.history_view),
                name='%sadmin_%s_%s_history' % info),
            url(r'^(.+)/delete/$',
                wrap(self.delete_view),
                name='%sadmin_%s_%s_delete' % info),
            url(r'^(.+)/$',
                wrap(self.change_view),
                name='%sadmin_%s_%s_change' % info),
        )

        return urlpatterns


    inline_formset_types = [(content_type, inlineformset_factory(Page, content_type, extra=1)) for content_type in PageContent.types]


    def change_view(self, request, object_id, extra_context=None):

        opts = self.model._meta
        #page = get_object_or_404(Page, pk=object_id)
        page = self.model._default_manager.get(pk=unquote(object_id))

        if not self.has_change_permission(request, page):
            raise PermissionDenied

        if request.method == 'POST':
            page_form = PageForm(request.POST, instance=page)

            inline_formsets = [
                formset_class(request.POST, instance=page, prefix=content_type.__name__.lower()) for content_type, formset_class in self.inline_formset_types
            ]

            if page_form.is_valid() and all([subform.is_valid() for subform in [formset for formset in inline_formsets]]):
                page_form.save()
                for formset in inline_formsets:
                    formset.save()
                return HttpResponseRedirect(".")
        else:
            page_form = PageForm(instance=page)
            inline_formsets = [
                formset_class(instance=page, prefix=content_type.__name__.lower()) for content_type, formset_class in self.inline_formset_types
            ]


        content_types = []
        for content_type in PageContent.types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name[:-8], content_name.replace(' ','')))

        context = {
            'has_file_field': False,
            'opts': opts,
            'page': page,
            'page_form': page_form,
            'inline_formsets': inline_formsets,
            'content_types': content_types,
        }

        return render_to_response("admin/feincms/page/change_form.html", context, context_instance=template.RequestContext(request))


def all(obj):
    if type(obj) == type([]):
        for item in obj:
            if not(all(item)):
                return False
    elif (not(obj)):
        return False
    return True


admin.site.register(Region,
    list_display=('key', 'inherited'),
    )
admin.site.register(Template,
    list_display=('title', 'path'),
    )
admin.site.register(Page, PageAdmin)


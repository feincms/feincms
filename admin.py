import re

from django import forms, template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.forms.formsets import all_valid
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext_lazy as _

from feincms.models import Region, Template, Page, PageContent


FEINCMS_ADMIN_MEDIA = getattr(settings, 'FEINCMS_ADMIN_MEDIA', '/media/sys/feincms/')


class PageForm(forms.ModelForm):
    class Meta:
        model = Page


class PageSettingsFieldset(forms.ModelForm):
    class Meta:
        model = Page
        exclude = ('active', 'template', 'title', 'in_navigation')


class PageAdmin(admin.ModelAdmin):
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


    inline_formset_types = [(
        content_type,
        inlineformset_factory(Page, content_type, extra=1)
        ) for content_type in PageContent.types]


    def change_view(self, request, object_id, extra_context=None):

        opts = self.model._meta
        page = self.model._default_manager.get(pk=unquote(object_id))

        if not self.has_change_permission(request, page):
            raise PermissionDenied

        if request.method == 'POST':
            page_form = PageForm(request.POST, instance=page)

            inline_formsets = [
                formset_class(request.POST, instance=page,
                    prefix=content_type.__name__.lower())
                for content_type, formset_class in self.inline_formset_types]

            if page_form.is_valid() and all_valid(inline_formsets):
                page_form.save()
                for formset in inline_formsets:
                    formset.save()
                return HttpResponseRedirect(".")

            settings_fieldset = PageSettingsFieldset(request.POST, instance=page)
            settings_fieldset.is_valid()
        else:
            page_form = PageForm(instance=page)
            inline_formsets = [
                formset_class(instance=page, prefix=content_type.__name__.lower())
                for content_type, formset_class in self.inline_formset_types]

            settings_fieldset = PageSettingsFieldset(instance=page)

        content_types = []
        for content_type in PageContent.types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name[:-8], content_name.replace(' ','')))

        context = {
            'has_file_field': True, # FIXME - but isn't fixed in django either
            'opts': opts,
            'page': page,
            'page_form': page_form,
            'inline_formsets': inline_formsets,
            'content_types': content_types,
            'settings_fieldset': settings_fieldset,
            'FEINCMS_ADMIN_MEDIA': FEINCMS_ADMIN_MEDIA,
        }

        return render_to_response("admin/feincms/page/change_form_edit.html",
            context, context_instance=template.RequestContext(request))


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


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
            #url(r'^$',
            #    wrap(self.frameset),
            #    name='%sadmin_%s_%s_frames' % info),
            #url(r'^tree/$',
            #    wrap(self.tree),
            #    name='%sadmin_%s_%s_tree' % info),
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

"""  
    def change_view(self, request, object_id, extra_context=None):
        model = self.model
        
        opts = model._meta
        obj = model._default_manager.get(pk=unquote(object_id))
        
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
            
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        exclude = []
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": [],
            "formfield_callback": self.formfield_for_dbfield,
        }
        ModelForm = modelform_factory(self.model)
        
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            for FormSet in self.get_formsets(request, new_object):
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object)
                formsets.append(formset)
            
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)
                
                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)
        
        else:
            form = ModelForm(instance=obj)
            for FormSet in self.get_formsets(request, obj):
                formset = FormSet(instance=obj)
                formsets.append(formset)
            
        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj), self.prepopulated_fields)
        media = self.media + adminForm.media
        
        projectForm = ProjectForm()
        RTCForm = RichTextContentForm()
        
        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media
            
        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'form': form,
            'projectForm': projectForm,
            'RTCForm': RTCForm,
            'object_id': object_id,
            'original': obj,
            'regions': models.Region.objects.all(),
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})

        return self.render_change_form(request, context, change=True, obj=obj)
    change_view = transaction.commit_on_success(change_view)  
 
  
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        ordered_objects = opts.get_ordered_objects()
        context.update({
            'add': add,
            'change': change,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'has_delete_permission': self.has_delete_permission(request, obj),
            'has_file_field': True, # FIXME - this should check if form or formsets have a FileField,
            'has_absolute_url': hasattr(self.model, 'get_absolute_url'),
            'ordered_objects': ordered_objects,
            'form_url': mark_safe(form_url),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model(self.model).id,
            'save_as': self.save_as,
            'save_on_top': self.save_on_top,
            'root_path': self.admin_site.root_path,
        })
        
        return render_to_response(self.change_form_template or [
            "admin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
            "admin/%s/change_form.html" % app_label,
            "admin/change_form.html"
        ], context, context_instance=template.RequestContext(request))        


    def frameset(self, request, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label

        if not self.has_change_permission(request, None):
            raise PermissionDenied

        context = {
            'root_path': self.admin_site.root_path,
            'app_label': app_label,
        }
        return render_to_response('admin/feincms/frameset.html',
            context, context_instance=RequestContext(request))

    def tree(self, request, extra_context=None):
        opts = self.model._meta
        app_label = opts.app_label

        if not self.has_change_permission(request, None):
            raise PermissionDenied

        context = {
            'root_path': self.admin_site.root_path,
            'app_label': app_label,

            'pages': models.Page.objects.all(),
        }

        return render_to_response('admin/feincms/tree.html',
            context, context_instance=RequestContext(request))

"""
admin.site.register(Region,
    list_display=('key', 'inherited'),
    )
admin.site.register(Template,
    list_display=('title', 'path'),
    )
admin.site.register(Page, PageAdmin)


import re

from django import forms, template
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import unquote
from django.core import serializers
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, transaction
from django.forms.formsets import all_valid
from django.forms.models import inlineformset_factory
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext_lazy as _



FEINCMS_ADMIN_MEDIA = getattr(settings, 'FEINCMS_ADMIN_MEDIA', '/media/sys/feincms/')


class ItemEditorMixin(object):
    """
    This mixin needs an attribute on the ModelAdmin class:

    show_on_top::
        A list of fields which should be displayed at the top of the form.
        This does not need to (and should not) include ``template''
    """

    def change_view(self, request, object_id, extra_context=None):

        if not hasattr(self.model, '_feincms_content_types'):
            raise ImproperlyConfigured, 'You need to create at least one content type for the %s model.' % (self.model.__name__)

        class ModelForm(forms.ModelForm):
            class Meta:
                model = self.model

        class SettingsFieldset(forms.ModelForm):
            # This form class is used solely for presentation, the data will be saved
            # by the ModelForm above

            class Meta:
                model = self.model
                exclude = self.show_on_top+('template',)

        inline_formset_types = [(
            content_type,
            inlineformset_factory(self.model, content_type, extra=1)
            ) for content_type in self.model._feincms_content_types]

        opts = self.model._meta
        app_label = opts.app_label
        obj = self.model._default_manager.get(pk=unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if request.method == 'POST':
            model_form = ModelForm(request.POST, request.FILES, instance=obj)

            inline_formsets = [
                formset_class(request.POST, request.FILES, instance=obj,
                    prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types]

            if model_form.is_valid() and all_valid(inline_formsets):
                model_form.save()
                for formset in inline_formsets:
                    formset.save()
                return HttpResponseRedirect(".")

            settings_fieldset = SettingsFieldset(request.POST, instance=obj)
            settings_fieldset.is_valid()
        else:
            model_form = ModelForm(instance=obj)
            inline_formsets = [
                formset_class(instance=obj, prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types]

            settings_fieldset = SettingsFieldset(instance=obj)

        content_types = []
        for content_type in self.model._feincms_content_types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name, content_type.__name__.lower()))

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'opts': opts,
            'page': obj,
            'page_form': model_form,
            'inline_formsets': inline_formsets,
            'content_types': content_types,
            'settings_fieldset': settings_fieldset,
            'top_fieldset': [model_form[field] for field in self.show_on_top],
            'FEINCMS_ADMIN_MEDIA': FEINCMS_ADMIN_MEDIA,
        }

        return render_to_response([
            'admin/feincms/%s/%s/item_editor.html' % (app_label, opts.object_name.lower()),
            'admin/feincms/%s/item_editor.html' % app_label,
            'admin/feincms/item_editor.html',
            ], context, context_instance=template.RequestContext(request))


class TreeEditorMixin(object):
    def changelist_view(self, request, extra_context=None):
        # handle AJAX requests
        if request.is_ajax():
            cmd = request.POST.get('__cmd')
            if cmd=='save_tree':
                return self._save_tree(request)
            elif cmd=='delete_item':
                return self._delete_item(request)

            return HttpResponse('Oops. AJAX request not understood.')

        from django.contrib.admin.views.main import ChangeList, ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label

        if not self.has_change_permission(request, None):
            raise PermissionDenied
        try:
            cl = ChangeList(request, self.model, self.list_display,
                self.list_display_links, self.list_filter, self.date_hierarchy,
                self.search_fields, self.list_select_related, self.list_per_page,
                self.list_editable, self)
        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given and
            # the 'invalid=1' parameter was already in the query string, something
            # is screwed up with the database, so display an error page.
            if ERROR_FLAG in request.GET.keys():
                return render_to_response('admin/invalid_setup.html', {'title': _('Database error')})
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        context = {
            'FEINCMS_ADMIN_MEDIA': FEINCMS_ADMIN_MEDIA,
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'has_add_permission': self.has_add_permission(request),
            'root_path': self.admin_site.root_path,
            'app_label': app_label,
            'object_list': self.model._tree_manager.all(),
        }
        context.update(extra_context or {})
        return render_to_response([
            'admin/feincms/%s/%s/tree_editor.html' % (app_label, opts.object_name.lower()),
            'admin/feincms/%s/tree_editor.html' % app_label,
            'admin/feincms/tree_editor.html',
            ], context, context_instance=template.RequestContext(request))

    def _save_tree(self, request):
        pagetree = simplejson.loads(request.POST['tree'])
        # 0 = tree_id, 1 = parent_id, 2 = left, 3 = right, 4 = level, 5 = item_id
        sql = "UPDATE %s SET %s=%%s, %s_id=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s" % (
            self.model._meta.db_table,
            self.model._meta.tree_id_attr,
            self.model._meta.parent_attr,
            self.model._meta.left_attr,
            self.model._meta.right_attr,
            self.model._meta.level_attr,
            self.model._meta.pk.column)

        connection.cursor().executemany(sql, pagetree)
        transaction.commit_unless_managed()

        return HttpResponse("OK", mimetype="text/plain")

    def _delete_item(self, request):
        page_id = request.POST['item_id']
        obj = self.model._default_manager.get(pk=unquote(page_id))
        obj.delete()
        return HttpResponse("OK", mimetype="text/plain")


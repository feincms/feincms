import re
import copy

from django import forms, template
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.db import transaction
from django.db.models import loading
from django.forms.formsets import all_valid
from django.forms.models import modelform_factory, inlineformset_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

from feincms import settings

FRONTEND_EDITING_MATCHER = re.compile(r'(\d+)\|(\w+)\|(\d+)')
FEINCMS_CONTENT_FIELDSET_NAME = 'FEINCMS_CONTENT'
FEINCMS_CONTENT_FIELDSET = (FEINCMS_CONTENT_FIELDSET_NAME, {'fields': ()})

csrf_protect_m = method_decorator(csrf_protect)


class ItemEditorForm(forms.ModelForm):
    region = forms.CharField(widget=forms.HiddenInput())
    ordering = forms.IntegerField(widget=forms.HiddenInput())


class ItemEditor(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        # Make sure all models are completely loaded before attempting to
        # proceed. The dynamic nature of FeinCMS models makes this necessary.
        # For more informations, have a look at issue #23 on github:
        # http://github.com/matthiask/feincms/issues#issue/23
        from django.core.management.validation import get_validation_errors
        from StringIO import StringIO
        get_validation_errors(StringIO(), None)

        super(ItemEditor, self).__init__(*args, **kwargs)

    def _formfield_callback(self, request):
        if settings.DJANGO10_COMPAT:
            # This should compare for Django SVN before [9761] (From 2009-01-16),
            # but I don't care that much. Doesn't work with git checkouts anyway, so...
            return self.formfield_for_dbfield
        else:
            return curry(self.formfield_for_dbfield, request=request)

    def _frontend_editing_view(self, request, cms_id, content_type, content_id):
        """
        This view is used strictly for frontend editing -- it is not used inside the
        standard administration interface.

        The code in feincms/templates/admin/feincms/fe_tools.html knows how to call
        this view correctly.
        """

        try:
            model_cls = loading.get_model(self.model._meta.app_label, content_type)
            obj = model_cls.objects.get(parent=cms_id, id=content_id)
        except:
            raise Http404

        form_class_base = getattr(model_cls, 'feincms_item_editor_form', ItemEditorForm)

        ModelForm = modelform_factory(model_cls,
            exclude=('parent', 'region', 'ordering'),
            form=form_class_base,
            formfield_callback=self._formfield_callback(request=request))

        # we do not want to edit these two fields in the frontend editing mode; we are
        # strictly editing single content blocks there.
        # We have to remove them from the form because we explicitly redefined them in
        # the ItemEditorForm definition above. Just using exclude is not enough.
        del ModelForm.base_fields['region']
        del ModelForm.base_fields['ordering']

        if request.method == 'POST':
            # The prefix is used to replace the formset identifier from the ItemEditor
            # interface. Customization of the form is easily possible through either matching
            # the prefix (frontend editing) or the formset identifier (ItemEditor) as it is
            # done in the richtext and mediafile init.html item editor includes.
            form = ModelForm(request.POST, instance=obj, prefix=content_type)

            if form.is_valid():
                obj = form.save()

                return render_to_response('admin/feincms/fe_editor_done.html', {
                    'content': obj.render(request=request),
                    'identifier': obj.fe_identifier(),
                    'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
                    'FEINCMS_ADMIN_MEDIA_HOTLINKING': settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
                    })
        else:
            form = ModelForm(instance=obj, prefix=content_type)

        return render_to_response('admin/feincms/fe_editor.html', {
            'frontend_editing': True,
            'title': _('Change %s') % force_unicode(model_cls._meta.verbose_name),
            'object': obj,
            'form': form,
            'is_popup': True,
            'media': self.media,
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
            }, context_instance=template.RequestContext(request,
                processors=self.model.feincms_item_editor_context_processors))

    def _get_inline_formset_types(self, request):
        return [(
            content_type,
            inlineformset_factory(self.model, content_type, extra=1,
                fk_name='parent', #added so multiple foreign keys are not a problem
                form=getattr(content_type, 'feincms_item_editor_form', ItemEditorForm),
                formfield_callback=self._formfield_callback(request=request))
            ) for content_type in self.model._feincms_content_types]

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, extra_context=None, form_url=None):
        opts = self.model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request,
            fields=None,
            formfield_callback=self._formfield_callback(request=request),
            form=self.form
        )

        inline_formset_types = self._get_inline_formset_types(request)
        formsets = []

        if request.method == 'POST':
            model_form = ModelForm(request.POST, request.FILES)

            if model_form.is_valid():
                form_validated = True
                new_object = self.save_form(request, model_form, change=False)
            else:
                form_validated = False
                new_object = self.model()

            inline_formsets = [
                formset_class(request.POST, request.FILES, instance=new_object,
                    prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types]

            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(data=request.POST, files=request.FILES,
                    instance=new_object,
                    save_as_new=request.POST.has_key('_saveasnew'),
                    prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)

            if all_valid(inline_formsets+formsets) and form_validated:
                self.save_model(request, new_object, model_form, change=False)
                model_form.save_m2m()
                for formset in inline_formsets:
                    formset.save()
                for formset in formsets:
                    self.save_formset(request, model_form, formset, change=False)

                msg = _('The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(new_object)}
                if request.POST.has_key("_continue"):
                    self.message_user(request, msg + ' ' + _("You may edit it again below."))
                    return HttpResponseRedirect('../%s/' % new_object.pk)
                elif request.POST.has_key('_addanother'):
                    self.message_user(request, msg + ' ' + (_("You may add another %s below.") % force_unicode(opts.verbose_name)))
                    return HttpResponseRedirect("../add/")
                else:
                    self.message_user(request, msg)
                    return HttpResponseRedirect("../")
        else:
            initial = dict(request.GET.items())
            model_form = ModelForm(initial=initial)
            inline_formsets = [
                formset_class(prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types]

            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request), self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=self.model(),
                    prefix=prefix, queryset=inline.queryset(request))
                formsets.append(formset)

        # Prepare mapping of content types to their prettified names
        content_types = []
        for content_type in self.model._feincms_content_types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name, content_type.__name__.lower()))

        context = {}

        #media = self.media + model_form.media
        adminForm = helpers.AdminForm(model_form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets,
                model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        if hasattr(self.model, '_feincms_templates'):
            context['available_templates'] = self.model._feincms_templates

        if hasattr(self.model, 'parent'):
            context['has_parent_attribute'] = True

        context.update({
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
            'add': True,
            'change': False,
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'opts': opts,
            'object': self.model(),
            'object_form': model_form,
            'adminform': adminForm,
            'inline_formsets': inline_formsets,
            'inline_admin_formsets': inline_admin_formsets,
            'content_types': content_types,
            'media': media,
            'errors': helpers.AdminErrorList(model_form, inline_formsets),
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
        })

        return self.render_item_editor(request, None, context)

    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        self.model._needs_content_types()

        # Recognize frontend editing requests
        # This is done here so that the developer does not need to add additional entries to
        # urls.py or something...
        res = FRONTEND_EDITING_MATCHER.search(object_id)

        if res:
            return self._frontend_editing_view(request, res.group(1), res.group(2), res.group(3))

        opts = self.model._meta

        try:
            obj = self.model._default_manager.get(pk=unquote(object_id))
        except self.model.DoesNotExist:
            raise Http404

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if "revision" in request.GET:
            from reversion.models import Revision

            try:
                revision = Revision.objects.get(pk=request.GET['revision'])
            except Revision.DoesNotExist:
                raise Http404

            self.message_user(request, _('Click save to replace the current content with this version'))
        else:
            revision = None

        ModelForm = self.get_form(
            request,
            obj,
            # NOTE: Fields *MUST* be set to None to avoid breaking
            # django.contrib.admin.option.ModelAdmin's default get_form()
            # will generate a very abbreviated field list which will cause
            # KeyErrors during clean() / save()
            fields=None,
            formfield_callback=self._formfield_callback(request=request),
            form=self.form
        )

        # generate a formset type for every concrete content type
        inline_formset_types = self._get_inline_formset_types(request)

        formsets = []
        if request.method == 'POST':
            FORM_DATA = {}
            model_form = ModelForm(request.POST, request.FILES, instance=obj)

            inline_formsets = [
                formset_class(request.POST, request.FILES, instance=obj,
                    prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types]

            if model_form.is_valid():
                form_validated = True
                new_object = self.save_form(request, model_form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            for FormSet in self.get_formsets(request, new_object):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix)
                formsets.append(formset)

            if all_valid(inline_formsets+formsets) and form_validated:
                #model_form.save(commit=False)
                model_form.save_m2m()
                for formset in inline_formsets:
                    formset.save()
                #model_form.save(commit=True)
                self.save_model(request, new_object, model_form, change=True)
                for formset in formsets:
                    self.save_formset(request, model_form, formset, change=True)

                msg = _('The %(name)s "%(obj)s" was changed successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
                if request.POST.has_key("_continue"):
                    self.message_user(request, msg + ' ' + _("You may edit it again below."))
                    return HttpResponseRedirect('.')
                elif request.POST.has_key('_addanother'):
                    self.message_user(request, msg + ' ' + (_("You may add another %s below.") % force_unicode(opts.verbose_name)))
                    return HttpResponseRedirect("../add/")
                else:
                    self.message_user(request, msg)
                    return HttpResponseRedirect("../")
        elif revision:
            FORM_DATA = {}

            total_forms = dict(
                [(ct.__name__.lower(), 0) for ct in self.model._feincms_content_types]
            )

            for version in revision.version_set.all().select_related("content_type"):
                if version.object_version.object == obj:
                    FORM_DATA.update(version.field_dict)
                    continue

                version_prefix = "%s-%s" % (
                    version.content_type.model,
                    total_forms[version.content_type.model]
                )


                for k, v in version.field_dict.items():
                    form_key = "%s-%s" % (version_prefix, k)
                    assert form_key not in FORM_DATA
                    FORM_DATA[form_key] = v

                # defaultdict would be cleaner but this works with Python 2.4:
                total_forms[version.content_type.model] += 1


            for k, v in total_forms.items():
                FORM_DATA["%s-INITIAL_FORMS" % k] = v
                # TOTAL FORMS should be one for each actual object and one for
                # the "Add new" feature. We'll bump the total up if we actually
                # have existing content:
                if v:
                    FORM_DATA["%s-TOTAL_FORMS" % k] = v + 1
                else:
                    FORM_DATA["%s-TOTAL_FORMS" % k] = 0

            # BUG: This somehow does not correctly initialize the initial form for adding new content correctly
            model_form = ModelForm(FORM_DATA, instance=obj)
            inline_formsets = [
                formset_class(FORM_DATA, instance=obj, prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types
            ]
            prefixes = {}
            for FormSet in self.get_formsets(request, obj):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix)
                formsets.append(formset)
        else:
            model_form = ModelForm(instance=obj)
            inline_formsets = [
                formset_class(instance=obj, prefix=content_type.__name__.lower())
                for content_type, formset_class in inline_formset_types
            ]
            prefixes = {}
            for FormSet in self.get_formsets(request, obj):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix)
                formsets.append(formset)

        # Prepare mapping of content types to their prettified names
        content_types = []
        for content_type in self.model._feincms_content_types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name, content_type.__name__.lower()))

        context = {}

        adminForm = helpers.AdminForm(model_form, self.get_fieldsets(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media


        if hasattr(self.model, '_feincms_templates'):
            context['available_templates'] = self.model._feincms_templates

        if hasattr(self.model, 'parent'):
            context['has_parent_attribute'] = True

        context.update({
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj=obj),
            'has_delete_permission': self.has_delete_permission(request, obj=obj),
            'add': False,
            'change': obj.pk is not None,
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'opts': opts,
            'object': obj,
            'object_form': model_form,
            'adminform': adminForm,
            'inline_formsets': inline_formsets,
            'inline_admin_formsets': inline_admin_formsets,
            'content_types': content_types,
            'media': media,
            'errors': helpers.AdminErrorList(model_form, inline_formsets),
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
            'FEINCMS_CONTENT_FIELDSET_NAME': FEINCMS_CONTENT_FIELDSET_NAME,
        })

        return self.render_item_editor(request, obj, context)

    def get_template_list(self):
        opts = self.model._meta
        return [
            'admin/feincms/%s/%s/item_editor.html' % (
                opts.app_label, opts.object_name.lower()),
            'admin/feincms/%s/item_editor.html' % opts.app_label,
            'admin/feincms/item_editor.html',
            ]
    
    def render_item_editor(self, request, object, context):
        return render_to_response(
            self.get_template_list(), context,
            context_instance=template.RequestContext(
                request,
                processors=self.model.feincms_item_editor_context_processors))

    def get_fieldsets(self, request, obj=None):
        """ Convert show_on_top to fieldset for backwards compatibility.

        Also insert FEINCMS_CONTENT_FIELDSET it not present.
        Is it reasonable to assume this should always be included?
        """

        fieldsets = copy.deepcopy(
            super(ItemEditor, self).get_fieldsets(request, obj))
        
        if not FEINCMS_CONTENT_FIELDSET_NAME in dict(fieldsets).keys():
            fieldsets.insert(0, FEINCMS_CONTENT_FIELDSET)
            
        if getattr(self, 'show_on_top', ()):
            if hasattr(self.model, '_feincms_templates'):
                if 'template_key' not in self.show_on_top:
                    self.show_on_top = ['template_key'] + \
                        list(self.show_on_top) 
            if self.declared_fieldsets:
                # check to ensure no duplicated fields
                all_fields = []
                for fieldset_data in dict(self.declared_fieldsets).values():
                    all_fields += list(fieldset_data.get('fields', ()))
                for field_name in self.show_on_top:
                    if field_name in all_fields:
                        raise ImproperlyConfigured(
                            'Field "%s" is present in both show_on_top and '
                            'fieldsets' % field_name)
            else: # no _declared_ fieldsets,
                # remove show_on_top fields from implicit fieldset
                for fieldset in fieldsets:
                    for field_name in self.show_on_top:
                        if field_name in fieldset[1]['fields']:
                            fieldset[1]['fields'].remove(field_name)
            fieldsets.insert(0, (None, {'fields': self.show_on_top}))

        return fieldsets

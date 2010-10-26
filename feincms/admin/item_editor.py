import re
import copy

from django import forms, template
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import loading
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.contrib.admin.options import InlineModelAdmin

from feincms import settings, ensure_completely_loaded

FRONTEND_EDITING_MATCHER = re.compile(r'(\d+)\|(\w+)\|(\d+)')
FEINCMS_CONTENT_FIELDSET_NAME = 'FEINCMS_CONTENT'
FEINCMS_CONTENT_FIELDSET = (FEINCMS_CONTENT_FIELDSET_NAME, {'fields': ()})


class ItemEditorForm(forms.ModelForm):
    region = forms.CharField(widget=forms.HiddenInput())
    ordering = forms.IntegerField(widget=forms.HiddenInput())


class FeinCMSInline(InlineModelAdmin):
    extra = 0
    fk_name = 'parent'
    template = 'admin/feincms/content_inline.html'

    def __init__(self, *args, **kwargs):
        super(FeinCMSInline, self).__init__(*args, **kwargs)
        self.verbose_name_plural = \
            u'Feincms_Inline: %s' % (self.verbose_name_plural,) # earmark


def get_feincms_inlines(model):
    """ Generate genuine django inlines for registered content types. """
    inlines = []
    for content_type in model._feincms_content_types:
        name = '%sFeinCMSInline' % content_type.__name__
        attrs = {
            '__module__': model.__module__,
            'model': content_type,
            'form': getattr(content_type, 'feincms_item_editor_form',
                            ItemEditorForm),
            }
        inlines.append(type(name, (FeinCMSInline,), attrs))
    return inlines


class ItemEditor(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        ensure_completely_loaded()

        super(ItemEditor, self).__init__(model, admin_site)

        # Add inline instances for FeinCMS content inlines
        for inline_class in get_feincms_inlines(model):
            inline_instance = inline_class(self.model, self.admin_site)
            self.inline_instances.append(inline_instance)

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
                    'FEINCMS_ADMIN_MEDIA_HOTLINKING': \
                        settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
                    'FEINCMS_JQUERY_NO_CONFLICT': \
                        settings.FEINCMS_JQUERY_NO_CONFLICT,
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
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': \
                settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
            'FEINCMS_JQUERY_NO_CONFLICT': settings.FEINCMS_JQUERY_NO_CONFLICT,
            }, context_instance=template.RequestContext(request,
                processors=self.model.feincms_item_editor_context_processors))

    def get_content_type_map(self):
        """ Prepare mapping of content types to their prettified names. """
        content_types = []
        for content_type in self.model._feincms_content_types:
            content_name = content_type._meta.verbose_name
            content_types.append((content_name, content_type.__name__.lower()))
        return content_types

    def get_extra_context(self, request):
        """ Return extra context parameters for add/change views. """

        extra_context = {
            'model': self.model,
            'available_templates':
                getattr(self.model, '_feincms_templates', ()),
            'has_parent_attribute': hasattr(self.model, 'parent'),
            'content_types': self.get_content_type_map(),
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING':
                settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
            'FEINCMS_JQUERY_NO_CONFLICT': settings.FEINCMS_JQUERY_NO_CONFLICT,
            'FEINCMS_CONTENT_FIELDSET_NAME': FEINCMS_CONTENT_FIELDSET_NAME,
            }

        for processor in self.model.feincms_item_editor_context_processors:
            extra_context.update(processor(request))

        return extra_context

    def add_view(self, request, form_url='', extra_context=None):
        context = {}

        # insert dummy object as 'original' so template code can grab defaults
        # for template, etc.
        context['original'] = self.model()

        # If there are errors in the form, we need to preserve the object's
        # template as it was set when the user attempted to save it, so that
        # the same regions appear on screen.
        if request.method == 'POST' and \
                hasattr(self.model, '_feincms_templates'):
            context['original'].template_key = request.POST['template_key']

        context.update(self.get_extra_context(request))
        context.update(extra_context or {})
        return super(ItemEditor, self).add_view(request, form_url, context)

    def change_view(self, request, object_id, extra_context=None):
        self.model._needs_content_types()

        # Recognize frontend editing requests
        # This is done here so that the developer does not need to add
        # additional entries to # urls.py or something...
        res = FRONTEND_EDITING_MATCHER.search(object_id)
        if res:
            return self._frontend_editing_view(
                request, res.group(1), res.group(2), res.group(3))

        context = {}
        context.update(self.get_extra_context(request))
        context.update(extra_context or {})
        return super(ItemEditor, self).change_view(request, object_id, context)

    @property
    def change_form_template(self):
        return self.get_template_list()

    def get_template_list(self):
        # retained for backwards-compatibility, change_form_template wraps it
        opts = self.model._meta
        return [
            'admin/feincms/%s/%s/item_editor.html' % (
                opts.app_label, opts.object_name.lower()),
            'admin/feincms/%s/item_editor.html' % opts.app_label,
            'admin/feincms/item_editor.html',
            ]

    def get_fieldsets(self, request, obj=None):
        """ Convert show_on_top to fieldset for backwards compatibility.

        Also insert FEINCMS_CONTENT_FIELDSET it not present.
        Is it reasonable to assume this should always be included?
        """

        fieldsets = copy.deepcopy(
            super(ItemEditor, self).get_fieldsets(request, obj))

        if not FEINCMS_CONTENT_FIELDSET_NAME in dict(fieldsets).keys():
            fieldsets.append(FEINCMS_CONTENT_FIELDSET)

        if getattr(self, 'show_on_top', ()):
            import warnings
            warnings.warn("The show_on_top will soon be removed; please "
                          "update your " "code to use fieldsets instead. ",
                          PendingDeprecationWarning)
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

# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import re
import copy

from django import forms, template
from django.contrib import admin
from django.db.models import loading
from django.forms.models import modelform_factory
from django.http import Http404
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.contrib.admin.options import InlineModelAdmin

from feincms import settings, ensure_completely_loaded
from feincms.signals import itemeditor_post_save_related

# ------------------------------------------------------------------------
FRONTEND_EDITING_MATCHER = re.compile(r'(\d+)\|(\w+)\|(\d+)')
FEINCMS_CONTENT_FIELDSET_NAME = 'FEINCMS_CONTENT'
FEINCMS_CONTENT_FIELDSET = (FEINCMS_CONTENT_FIELDSET_NAME, {'fields': ()})

# ------------------------------------------------------------------------
class ItemEditorForm(forms.ModelForm):
    """
    The item editor form contains hidden region and ordering fields and should
    be used for all content type inlines.
    """

    region = forms.CharField(widget=forms.HiddenInput())
    ordering = forms.IntegerField(widget=forms.HiddenInput())

# ------------------------------------------------------------------------
class FeinCMSInline(InlineModelAdmin):
    """
    Custom ``InlineModelAdmin`` subclass used for content types.
    """

    form = ItemEditorForm
    extra = 0
    fk_name = 'parent'
    template = 'admin/feincms/content_inline.html'

# ------------------------------------------------------------------------
class ItemEditor(admin.ModelAdmin):
    """
    The ``ItemEditor`` is a drop-in replacement for ``ModelAdmin`` with the
    speciality of knowing how to work with :class:`feincms.models.Base`
    subclasses and associated content types.

    It does not have any public API except from everything inherited from'
    the standard ``ModelAdmin`` class.
    """

    def __init__(self, model, admin_site):
        ensure_completely_loaded()

        super(ItemEditor, self).__init__(model, admin_site)

        if hasattr(self, 'inline_instances'):
            # Add inline instances for FeinCMS content inlines
            # This works in Django 1.3 and lower
            # In Django 1.4 inline instances are generated using overridden get_inline_instances()
            self.append_feincms_inlines(self.inline_instances)

    def get_inline_instances(self, request):
        inline_instances = super(ItemEditor, self).get_inline_instances(request)
        self.append_feincms_inlines(inline_instances)

        return inline_instances

    def append_feincms_inlines(self, inline_instances):
        """ Append generated FeinCMS content inlines to native django inlines. """
        for inline_class in self.get_feincms_inlines(self.model):
            inline_instance = inline_class(self.model, self.admin_site)
            inline_instances.append(inline_instance)

    def get_feincms_inlines(self, model):
        """ Generate genuine django inlines for registered content types. """
        model._needs_content_types()

        inlines = []
        for content_type in model._feincms_content_types:
            attrs = {
                '__module__': model.__module__,
                'model': content_type,
                }

            if hasattr(content_type, 'feincms_item_editor_inline'):
                inline = content_type.feincms_item_editor_inline
                attrs['form'] = inline.form

                if hasattr(content_type, 'feincms_item_editor_form'):
                    import warnings
                    warnings.warn(
                        'feincms_item_editor_form on %s is ignored because feincms_item_editor_inline is set too' % content_type,
                        RuntimeWarning)

            else:
                inline = FeinCMSInline
                attrs['form'] = getattr(content_type,
                    'feincms_item_editor_form', inline.form)

            name = '%sFeinCMSInline' % content_type.__name__
            inlines.append(type(name, (inline,), attrs))
        return inlines

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
            formfield_callback=curry(self.formfield_for_dbfield, request=request))

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
                    'FEINCMS_JQUERY_NO_CONFLICT': \
                        settings.FEINCMS_JQUERY_NO_CONFLICT,
                    }, context_instance=template.RequestContext(request))
        else:
            form = ModelForm(instance=obj, prefix=content_type)

        context = self.get_extra_context(request)
        context.update({
            'frontend_editing': True,
            'title': _('Change %s') % force_unicode(model_cls._meta.verbose_name),
            'object': obj,
            'form': form,
            'is_popup': True,
            'media': self.media,
            })

        return render_to_response('admin/feincms/fe_editor.html', context,
            context_instance=template.RequestContext(request))

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
            'FEINCMS_JQUERY_NO_CONFLICT': settings.FEINCMS_JQUERY_NO_CONFLICT,
            'FEINCMS_CONTENT_FIELDSET_NAME': FEINCMS_CONTENT_FIELDSET_NAME,

            'FEINCMS_FRONTEND_EDITING': settings.FEINCMS_FRONTEND_EDITING,
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
        return super(ItemEditor, self).add_view(request, form_url, extra_context=context)

    def change_view(self, request, object_id, extra_context=None):
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
        return super(ItemEditor, self).change_view(request, object_id, extra_context=context)

    # The next two add support for sending a "saving done" signal as soon
    # as all relevant data have been saved (especially all foreign key relations)
    # This can be used to keep functionality dependend on item content happy.
    # NOTE: These two can (and probably should) be replaced by overriding
    # `save_related` as soon as we don't depend on Django<1.4 any more.
    def response_add(self, request, obj, *args, **kwargs):
        r = super(ItemEditor, self).response_add(request, obj, *args, **kwargs)
        itemeditor_post_save_related.send(sender=obj.__class__, instance=obj, created=True)
        return r

    def response_change(self, request, obj, *args, **kwargs):
        r = super(ItemEditor, self).response_change(request, obj, *args, **kwargs)
        itemeditor_post_save_related.send(sender=obj.__class__, instance=obj, created=False)
        return r

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
        """
        Insert FEINCMS_CONTENT_FIELDSET it not present.
        Is it reasonable to assume this should always be included?
        """

        fieldsets = copy.deepcopy(
            super(ItemEditor, self).get_fieldsets(request, obj))

        if not FEINCMS_CONTENT_FIELDSET_NAME in dict(fieldsets).keys():
            fieldsets.append(FEINCMS_CONTENT_FIELDSET)

        return fieldsets

    # These next are only used if later we use a subclass of this class
    # which also inherits from VersionAdmin.
    revision_form_template = "admin/feincms/revision_form.html"

    recover_form_template = "admin/feincms/recover_form.html"

    def render_revision_form(self, request, obj, version, context, revert=False, recover=False):
        context.update(self.get_extra_context(request))
        return super(ItemEditor, self).render_revision_form(request, obj, version, context, revert, recover)

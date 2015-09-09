# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import copy
import logging
import warnings

from django import forms
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.utils import unquote
from django.contrib.auth import get_permission_codename
from django.http import Http404

from feincms import ensure_completely_loaded
from feincms.extensions import ExtensionModelAdmin
from feincms.signals import itemeditor_post_save_related


# ------------------------------------------------------------------------
FEINCMS_CONTENT_FIELDSET_NAME = 'FEINCMS_CONTENT'
FEINCMS_CONTENT_FIELDSET = (FEINCMS_CONTENT_FIELDSET_NAME, {'fields': ()})

logger = logging.getLogger(__name__)


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
class ItemEditor(ExtensionModelAdmin):
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

    def get_inline_instances(self, request, *args, **kwargs):
        inline_instances = super(ItemEditor, self).get_inline_instances(
            request, *args, **kwargs)
        self.append_feincms_inlines(inline_instances, request)
        return inline_instances

    def append_feincms_inlines(self, inline_instances, request):
        """
        Append generated FeinCMS content inlines to native django inlines.
        """
        for inline_class in self.get_feincms_inlines(self.model, request):
            inline_instance = inline_class(self.model, self.admin_site)
            inline_instances.append(inline_instance)

    def can_add_content(self, request, content_type):
        perm = '.'.join((
            content_type._meta.app_label,
            get_permission_codename('add', content_type._meta)))
        return request.user.has_perm(perm)

    def get_feincms_inlines(self, model, request):
        """ Generate genuine django inlines for registered content types. """
        model._needs_content_types()

        inlines = []
        for content_type in model._feincms_content_types:
            if not self.can_add_content(request, content_type):
                continue

            attrs = {
                '__module__': model.__module__,
                'model': content_type,
            }

            if hasattr(content_type, 'feincms_item_editor_inline'):
                inline = content_type.feincms_item_editor_inline
                attrs['form'] = inline.form

                if hasattr(content_type, 'feincms_item_editor_form'):
                    warnings.warn(
                        'feincms_item_editor_form on %s is ignored because '
                        'feincms_item_editor_inline is set too' % content_type,
                        RuntimeWarning)

            else:
                inline = FeinCMSInline
                attrs['form'] = getattr(
                    content_type, 'feincms_item_editor_form', inline.form)

            name = '%sFeinCMSInline' % content_type.__name__
            # TODO: We generate a new class every time. Is that really wanted?
            inline_class = type(str(name), (inline,), attrs)
            inlines.append(inline_class)
        return inlines

    def get_content_type_map(self, request):
        """ Prepare mapping of content types to their prettified names. """
        content_types = []
        for content_type in self.model._feincms_content_types:
            if self.model == content_type._feincms_content_class:
                content_name = content_type._meta.verbose_name
                content_types.append(
                    (content_name, content_type.__name__.lower()))
        return content_types

    def get_extra_context(self, request):
        """ Return extra context parameters for add/change views. """

        extra_context = {
            'request': request,
            'model': self.model,
            'available_templates': getattr(
                self.model, '_feincms_templates', ()),
            'has_parent_attribute': hasattr(self.model, 'parent'),
            'content_types': self.get_content_type_map(request),
            'FEINCMS_CONTENT_FIELDSET_NAME': FEINCMS_CONTENT_FIELDSET_NAME,
        }

        for processor in self.model.feincms_item_editor_context_processors:
            extra_context.update(processor(request))

        return extra_context

    def add_view(self, request, **kwargs):
        if not self.has_add_permission(request):
            logger.warning(
                "Denied adding %s to \"%s\" (no add permission)",
                self.model,
                request.user
            )
            raise Http404

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
        context.update(kwargs.get('extra_context', {}))
        kwargs['extra_context'] = context
        return super(ItemEditor, self).add_view(request, **kwargs)

    def render_change_form(self, request, context, **kwargs):
        if kwargs.get('add'):
            if request.method == 'GET' and 'adminform' in context:
                if 'template_key' in context['adminform'].form.initial:
                    context['original'].template_key = (
                        context['adminform'].form.initial['template_key'])
                # ensure that initially-selected template in form is also
                # used to render the initial regions in the item editor
        return super(
            ItemEditor, self).render_change_form(request, context, **kwargs)

    def change_view(self, request, object_id, **kwargs):
        obj = self.get_object(request, unquote(object_id))
        if not self.has_change_permission(request, obj):
            logger.warning(
                "Denied editing %s to \"%s\" (no edit permission)",
                self.model,
                request.user
            )
            raise Http404

        context = {}
        context.update(self.get_extra_context(request))
        context.update(kwargs.get('extra_context', {}))
        kwargs['extra_context'] = context
        return super(ItemEditor, self).change_view(
            request, object_id, **kwargs)

    def save_related(self, request, form, formset, change):
        super(ItemEditor, self).save_related(
            request, form, formset, change)
        itemeditor_post_save_related.send(
            sender=form.instance.__class__,
            instance=form.instance,
            created=not change)

    @property
    def change_form_template(self):
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
            super(ItemEditor, self).get_fieldsets(request, obj)
        )
        names = [f[0] for f in fieldsets]

        if FEINCMS_CONTENT_FIELDSET_NAME not in names:
            fieldsets.append(FEINCMS_CONTENT_FIELDSET)

        return fieldsets

    # These next are only used if later we use a subclass of this class
    # which also inherits from VersionAdmin.
    revision_form_template = "admin/feincms/revision_form.html"

    recover_form_template = "admin/feincms/recover_form.html"

    def render_revision_form(self, request, obj, version, context,
                             revert=False, recover=False):
        context.update(self.get_extra_context(request))
        return super(ItemEditor, self).render_revision_form(
            request, obj, version, context, revert, recover)

# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import

from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from feincms import ensure_completely_loaded
from feincms.admin import item_editor, tree_editor

# ------------------------------------------------------------------------
from .forms import PageAdminForm
from .models import Page

# ------------------------------------------------------------------------
class PageAdmin(item_editor.ItemEditor, tree_editor.TreeEditor):
    class Media:
        css = {}
        js = []

    form = PageAdminForm

    # the fieldsets config here is used for the add_view, it has no effect
    # for the change_view which is completely customized anyway
    unknown_fields = ['template_key', 'parent', 'override_url', 'redirect_to']
    fieldset_insertion_index = 2
    fieldsets = [
        (None, {
            'fields': [
                ('title', 'slug'),
                ('active', 'in_navigation'),
                ],
        }),
        (_('Other options'), {
            'classes': ['collapse',],
            'fields': unknown_fields,
        }),
        # <-- insertion point, extensions appear here, see insertion_index above
        item_editor.FEINCMS_CONTENT_FIELDSET,
        ]
    readonly_fields = []
    list_display = ['short_title', 'is_visible_admin', 'in_navigation_toggle', 'template']
    list_filter = ['active', 'in_navigation', 'template_key', 'parent']
    search_fields = ['title', 'slug']
    prepopulated_fields = { 'slug': ('title',), }

    raw_id_fields = ['parent']
    radio_fields = {'template_key': admin.HORIZONTAL}

    @classmethod
    def add_extension_options(cls, *f):
        if isinstance(f[-1], dict):     # called with a fieldset
            cls.fieldsets.insert(cls.fieldset_insertion_index, f)
            f[1]['classes'] = list(f[1].get('classes', []))
            f[1]['classes'].append('collapse')
        else:   # assume called with "other" fields
            cls.fieldsets[1][1]['fields'].extend(f)

    def __init__(self, *args, **kwargs):
        ensure_completely_loaded()

        if len(Page._feincms_templates) > 4 and 'template_key' in self.radio_fields:
            del(self.radio_fields['template_key'])

        super(PageAdmin, self).__init__(*args, **kwargs)

        # The use of fieldsets makes only fields explicitly listed in there
        # actually appear in the admin form. However, extensions should not be
        # aware that there is a fieldsets structure and even less modify it;
        # we therefore enumerate all of the model's field and forcibly add them
        # to the last section in the admin. That way, nobody is left behind.
        from django.contrib.admin.util import flatten_fieldsets
        present_fields = flatten_fieldsets(self.fieldsets)

        for f in self.model._meta.fields:
            if not f.name.startswith('_') and not f.name in ('id', 'lft', 'rght', 'tree_id', 'level') and \
                    not f.auto_created and not f.name in present_fields and f.editable:
                self.unknown_fields.append(f.name)
                if not f.editable:
                    self.readonly_fields.append(f.name)

    in_navigation_toggle = tree_editor.ajax_editable_boolean('in_navigation', _('in navigation'))

    def _actions_column(self, page):
        editable = getattr(page, 'feincms_editable', True)

        preview_url = "../../r/%s/%s/" % (
                ContentType.objects.get_for_model(self.model).id,
                page.id)
        actions = super(PageAdmin, self)._actions_column(page)
        if editable:
            actions.insert(0, u'<a href="add/?parent=%s" title="%s"><img src="%sfeincms/img/icon_addlink.gif" alt="%s"></a>' % (
                page.pk, _('Add child page'), django_settings.STATIC_URL, _('Add child page')))
        actions.insert(0, u'<a href="%s" title="%s"><img src="%sfeincms/img/selector-search.gif" alt="%s" /></a>' % (
            preview_url, _('View on site'), django_settings.STATIC_URL, _('View on site')))

        return actions

    def add_view(self, request, **kwargs):
        # Preserve GET parameters
        kwargs['form_url'] = request.get_full_path()
        return super(PageAdmin, self).add_view(request, **kwargs)

    def response_add(self, request, obj, *args, **kwargs):
        response = super(PageAdmin, self).response_add(request, obj, *args, **kwargs)
        if 'parent' in request.GET and '_addanother' in request.POST and response.status_code in (301, 302):
            # Preserve GET parameters if we are about to add another page
            response['Location'] += '?parent=%s' % request.GET['parent']
        if 'translation_of' in request.GET:
            # Copy all contents
            for content_type in obj._feincms_content_types:
                if content_type.objects.filter(parent=obj).exists():
                    # Short-circuit processing -- don't copy any contents if
                    # newly added object already has some
                    return response

            try:
                original = self.model._tree_manager.get(pk=request.GET.get('translation_of'))
                original = original.original_translation
                obj.copy_content_from(original)
                obj.save()

                self.message_user(request, _('The content from the original translation has been copied to the newly created page.'))
            except (AttributeError, self.model.DoesNotExist):
                pass

        return response

    def _refresh_changelist_caches(self, *args, **kwargs):
        self._visible_pages = list(self.model.objects.active().values_list('id', flat=True))

    def change_view(self, request, object_id, **kwargs):
        try:
            return super(PageAdmin, self).change_view(request, object_id, **kwargs)
        except PermissionDenied:
            from django.contrib import messages
            messages.add_message(request, messages.ERROR, _("You don't have the necessary permissions to edit this object"))
        return HttpResponseRedirect(reverse('admin:page_page_changelist'))

    def is_visible_admin(self, page):
        """
        Instead of just showing an on/off boolean, also indicate whether this
        page is not visible because of publishing dates or inherited status.
        """
        if not hasattr(self, "_visible_pages"):
            self._visible_pages = list() # Sanity check in case this is not already defined

        if page.parent_id and not page.parent_id in self._visible_pages:
            # parent page's invisibility is inherited
            if page.id in self._visible_pages:
                self._visible_pages.remove(page.id)
            return tree_editor.ajax_editable_boolean_cell(page, 'active', override=False, text=_('inherited'))

        if page.active and not page.id in self._visible_pages:
            # is active but should not be shown, so visibility limited by extension: show a "not active"
            return tree_editor.ajax_editable_boolean_cell(page, 'active', override=False, text=_('extensions'))

        return tree_editor.ajax_editable_boolean_cell(page, 'active')
    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('is active')
    is_visible_admin.editable_boolean_field = 'active'

    # active toggle needs more sophisticated result function
    def is_visible_recursive(self, page):
        retval = []
        for c in page.get_descendants(include_self=True):
            retval.append(self.is_visible_admin(c))
        return retval
    is_visible_admin.editable_boolean_result = is_visible_recursive

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

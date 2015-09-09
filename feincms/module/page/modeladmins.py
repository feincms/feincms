# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from threading import local

from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.contrib import admin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _

from feincms import ensure_completely_loaded
from feincms import settings
from feincms.admin import item_editor, tree_editor

# ------------------------------------------------------------------------
from .forms import PageAdminForm


_local = local()


# ------------------------------------------------------------------------
class PageAdmin(item_editor.ItemEditor, tree_editor.TreeEditor):
    class Media:
        css = {}
        js = []

    form = PageAdminForm

    fieldset_insertion_index = 2
    fieldsets = [
        (None, {
            'fields': [
                ('title', 'slug'),
                ('active', 'in_navigation'),
            ],
        }),
        (_('Other options'), {
            'classes': ['collapse'],
            'fields': [
                'template_key', 'parent', 'override_url', 'redirect_to'],
        }),
        # <-- insertion point, extensions appear here, see insertion_index
        # above
        item_editor.FEINCMS_CONTENT_FIELDSET,
    ]
    readonly_fields = []
    list_display = [
        'short_title', 'is_visible_admin', 'in_navigation_toggle', 'template']
    list_filter = ['active', 'in_navigation', 'template_key', 'parent']
    search_fields = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}

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

    def __init__(self, model, admin_site):
        ensure_completely_loaded()

        if len(model._feincms_templates) > 4 and \
                'template_key' in self.radio_fields:
            del(self.radio_fields['template_key'])

        super(PageAdmin, self).__init__(model, admin_site)

    in_navigation_toggle = tree_editor.ajax_editable_boolean(
        'in_navigation', _('in navigation'))

    def get_readonly_fields(self, request, obj=None):
        readonly = super(PageAdmin, self).get_readonly_fields(request, obj=obj)
        if not settings.FEINCMS_SINGLETON_TEMPLATE_CHANGE_ALLOWED:
            if obj and obj.template and obj.template.singleton:
                return tuple(readonly) + ('template_key',)
        return readonly

    def get_form(self, *args, **kwargs):
        form = super(PageAdmin, self).get_form(*args, **kwargs)
        return curry(form, modeladmin=self)

    def _actions_column(self, page):
        addable = getattr(page, 'feincms_addable', True)

        preview_url = "../../r/%s/%s/" % (
            ContentType.objects.get_for_model(self.model).id,
            page.id)
        actions = super(PageAdmin, self)._actions_column(page)

        if addable:
            if not page.template.enforce_leaf:
                actions.insert(
                    0,
                    '<a href="add/?parent=%s" title="%s">'
                    '<img src="%s" alt="%s" />'
                    '</a>' % (
                        page.pk,
                        _('Add child page'),
                        static('feincms/img/icon_addlink.gif'),
                        _('Add child page'),
                    )
                )
        actions.insert(
            0,
            '<a href="%s" title="%s">'
            '<img src="%s" alt="%s" />'
            '</a>' % (
                preview_url,
                _('View on site'),
                static('feincms/img/selector-search.gif'),
                _('View on site'),
            )
        )
        return actions

    def add_view(self, request, **kwargs):
        kwargs['form_url'] = request.get_full_path()  # Preserve GET parameters
        if 'translation_of' in request.GET and 'language' in request.GET:
            try:
                original = self.model._tree_manager.get(
                    pk=request.GET.get('translation_of'))
            except (AttributeError, self.model.DoesNotExist):
                pass
            else:
                language_code = request.GET['language']
                language = dict(
                    django_settings.LANGUAGES).get(language_code, '')
                kwargs['extra_context'] = {
                    'adding_translation': True,
                    'title': _(
                        'Add %(language)s translation of "%(page)s"') % {
                        'language': language,
                        'page': original,
                    },
                    'language_name': language,
                    'translation_of': original,
                }
        return super(PageAdmin, self).add_view(request, **kwargs)

    def response_add(self, request, obj, *args, **kwargs):
        response = super(PageAdmin, self).response_add(
            request, obj, *args, **kwargs)
        if ('parent' in request.GET and
                '_addanother' in request.POST and
                response.status_code in (301, 302)):
            # Preserve GET parameters if we are about to add another page
            response['Location'] += '?parent=%s' % request.GET['parent']

        if ('translation_of' in request.GET and
                '_copy_content_from_original' in request.POST):
            # Copy all contents
            for content_type in obj._feincms_content_types:
                if content_type.objects.filter(parent=obj).exists():
                    # Short-circuit processing -- don't copy any contents if
                    # newly added object already has some
                    return response

            try:
                original = self.model._tree_manager.get(
                    pk=request.GET.get('translation_of'))
                original = original.original_translation
                obj.copy_content_from(original)
                obj.save()

                self.message_user(request, _(
                    'The content from the original translation has been copied'
                    ' to the newly created page.'))
            except (AttributeError, self.model.DoesNotExist):
                pass

        return response

    def change_view(self, request, object_id, **kwargs):
        try:
            return super(PageAdmin, self).change_view(
                request, object_id, **kwargs)
        except PermissionDenied:
            messages.add_message(
                request,
                messages.ERROR,
                _(
                    "You don't have the necessary permissions to edit this"
                    " object"
                )
            )
        return HttpResponseRedirect(reverse('admin:page_page_changelist'))

    def has_delete_permission(self, request, obj=None):
        if not settings.FEINCMS_SINGLETON_TEMPLATE_DELETION_ALLOWED:
            if obj and obj.template.singleton:
                return False
        return super(PageAdmin, self).has_delete_permission(request, obj=obj)

    def changelist_view(self, request, *args, **kwargs):
        _local.visible_pages = list(
            self.model.objects.active().values_list('id', flat=True))
        return super(PageAdmin, self).changelist_view(request, *args, **kwargs)

    def is_visible_admin(self, page):
        """
        Instead of just showing an on/off boolean, also indicate whether this
        page is not visible because of publishing dates or inherited status.
        """
        if page.parent_id and page.parent_id not in _local.visible_pages:
            # parent page's invisibility is inherited
            if page.id in _local.visible_pages:
                _local.visible_pages.remove(page.id)
            return tree_editor.ajax_editable_boolean_cell(
                page, 'active', override=False, text=_('inherited'))

        if page.active and page.id not in _local.visible_pages:
            # is active but should not be shown, so visibility limited by
            # extension: show a "not active"
            return tree_editor.ajax_editable_boolean_cell(
                page, 'active', override=False, text=_('extensions'))

        return tree_editor.ajax_editable_boolean_cell(page, 'active')
    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('is active')
    is_visible_admin.editable_boolean_field = 'active'

    # active toggle needs more sophisticated result function
    def is_visible_recursive(self, page):
        # Have to refresh visible_pages here, because TreeEditor.toggle_boolean
        # will have changed the value when inside this code path.
        _local.visible_pages = list(
            self.model.objects.active().values_list('id', flat=True))

        retval = []
        for c in page.get_descendants(include_self=True):
            retval.append(self.is_visible_admin(c))
        return retval
    is_visible_admin.editable_boolean_result = is_visible_recursive

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

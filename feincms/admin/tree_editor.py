# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from functools import reduce
import json
import logging

from django.contrib.admin.views import main
from django.contrib.admin.actions import delete_selected
from django.contrib.auth import get_permission_codename
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.http import (
    HttpResponse, HttpResponseBadRequest,
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError)
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.encoding import force_text

from mptt.exceptions import InvalidMove
from mptt.forms import MPTTAdminForm

from feincms import settings
from feincms.extensions import ExtensionModelAdmin


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------
def django_boolean_icon(field_val, alt_text=None, title=None):
    """
    Return HTML code for a nice representation of true/false.
    """

    # Origin: contrib/admin/templatetags/admin_list.py
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    alt_text = alt_text or BOOLEAN_MAPPING[field_val]
    if title is not None:
        title = 'title="%s" ' % title
    else:
        title = ''
    icon_url = static('feincms/img/icon-%s.gif' % BOOLEAN_MAPPING[field_val])
    return mark_safe(
        '<img src="%s" alt="%s" %s/>' % (icon_url, alt_text, title))


def _build_tree_structure(queryset):
    """
    Build an in-memory representation of the item tree, trying to keep
    database accesses down to a minimum. The returned dictionary looks like
    this (as json dump):

        {"6": [7, 8, 10]
         "7": [12],
         "8": [],
         ...
         }
    """
    all_nodes = {}

    mptt_opts = queryset.model._mptt_meta
    items = queryset.order_by(
        mptt_opts.tree_id_attr,
        mptt_opts.left_attr,
    ).values_list(
        "pk",
        "%s_id" % mptt_opts.parent_attr,
    )
    for p_id, parent_id in items:
        all_nodes.setdefault(
            str(parent_id) if parent_id else 0,
            [],
        ).append(p_id)
    return all_nodes


# ------------------------------------------------------------------------
def ajax_editable_boolean_cell(item, attr, text='', override=None):
    """
    Generate a html snippet for showing a boolean value on the admin page.
    Item is an object, attr is the attribute name we should display. Text
    is an optional explanatory text to be included in the output.

    This function will emit code to produce a checkbox input with its state
    corresponding to the item.attr attribute if no override value is passed.
    This input is wired to run a JS ajax updater to toggle the value.

    If override is passed in, ignores the attr attribute and returns a
    static image for the override boolean with no user interaction possible
    (useful for "disabled and you can't change it" situations).
    """
    if text:
        text = '&nbsp;(%s)' % text

    if override is not None:
        a = [django_boolean_icon(override, text), text]
    else:
        value = getattr(item, attr)
        a = [
            '<input type="checkbox" data-inplace data-inplace-id="%s"'
            ' data-inplace-attribute="%s" %s>' % (
                item.pk,
                attr,
                'checked="checked"' if value else '',
            )]

    a.insert(0, '<div id="wrap_%s_%d">' % (attr, item.pk))
    a.append('</div>')
    return mark_safe(''.join(a))


# ------------------------------------------------------------------------
def ajax_editable_boolean(attr, short_description):
    """
    Convenience function: Assign the return value of this method to a variable
    of your ModelAdmin class and put the variable name into list_display.

    Example::

        class MyTreeEditor(TreeEditor):
            list_display = ('__str__', 'active_toggle')

            active_toggle = ajax_editable_boolean('active', _('is active'))
    """
    def _fn(self, item):
        return ajax_editable_boolean_cell(item, attr)
    _fn.short_description = short_description
    _fn.editable_boolean_field = attr
    return _fn


# ------------------------------------------------------------------------
class ChangeList(main.ChangeList):
    """
    Custom ``ChangeList`` class which ensures that the tree entries are always
    ordered in depth-first order (order by ``tree_id``, ``lft``).
    """

    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        super(ChangeList, self).__init__(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        mptt_opts = self.model._mptt_meta
        qs = super(ChangeList, self).get_queryset(*args, **kwargs).\
            order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)
        # Force has_filters, so that the expand/collapse in sidebar is visible
        self.has_filters = True
        return qs

    def get_results(self, request):
        mptt_opts = self.model._mptt_meta
        if settings.FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS:
            clauses = [
                Q(**{
                    mptt_opts.tree_id_attr: tree_id,
                    mptt_opts.left_attr + '__lte': lft,
                    mptt_opts.right_attr + '__gte': rght,
                }) for lft, rght, tree_id in self.queryset.values_list(
                    mptt_opts.left_attr,
                    mptt_opts.right_attr,
                    mptt_opts.tree_id_attr,
                )
            ]
            # We could optimise a bit here by explicitely filtering out
            # any clauses that are for parents of nodes included in the
            # queryset anyway. (ie: drop all clauses that refer to a node
            # that is a parent to another node)

            if clauses:
                # Note: Django ORM is smart enough to drop additional
                # clauses if the initial query set is unfiltered. This
                # is good.
                self.queryset |= self.model._default_manager.filter(
                    reduce(lambda p, q: p | q, clauses),
                )

        super(ChangeList, self).get_results(request)

        # Pre-process permissions because we still have the request here,
        # which is not passed in later stages in the tree editor
        for item in self.result_list:
            item.feincms_changeable = self.model_admin.has_change_permission(
                request, item)

            item.feincms_addable = (
                item.feincms_changeable and
                self.model_admin.has_add_permission(request, item))


# ------------------------------------------------------------------------
class TreeEditor(ExtensionModelAdmin):
    """
    The ``TreeEditor`` modifies the standard Django administration change list
    to a drag-drop enabled interface for django-mptt_-managed Django models.

    .. _django-mptt: https://github.com/django-mptt/django-mptt/
    """

    form = MPTTAdminForm

    if settings.FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS:
        # Make sure that no pagination is displayed. Slicing is disabled
        # anyway, therefore this value does not have an influence on the
        # queryset
        list_per_page = 999999999

    def __init__(self, *args, **kwargs):
        super(TreeEditor, self).__init__(*args, **kwargs)

        self.list_display = list(self.list_display)

        if 'indented_short_title' not in self.list_display:
            if self.list_display[0] == 'action_checkbox':
                self.list_display[1] = 'indented_short_title'
            else:
                self.list_display[0] = 'indented_short_title'
        self.list_display_links = ('indented_short_title',)

        opts = self.model._meta
        self.change_list_template = [
            'admin/feincms/%s/%s/tree_editor.html' % (
                opts.app_label, opts.object_name.lower()),
            'admin/feincms/%s/tree_editor.html' % opts.app_label,
            'admin/feincms/tree_editor.html',
        ]
        self.object_change_permission =\
            opts.app_label + '.' + get_permission_codename('change', opts)
        self.object_add_permission =\
            opts.app_label + '.' + get_permission_codename('add', opts)
        self.object_delete_permission =\
            opts.app_label + '.' + get_permission_codename('delete', opts)

    def changeable(self, item):
        return getattr(item, 'feincms_changeable', True)

    def indented_short_title(self, item):
        """
        Generate a short title for an object, indent it depending on
        the object's depth in the hierarchy.
        """
        mptt_opts = item._mptt_meta
        r = ''
        try:
            url = item.get_absolute_url()
        except (AttributeError,):
            url = None

        if url:
            r = (
                '<input type="hidden" class="medialibrary_file_path"'
                ' value="%s" id="_refkey_%d" />') % (url, item.pk)

        changeable_class = ''
        if not self.changeable(item):
            changeable_class = ' tree-item-not-editable'
        tree_root_class = ''
        if not item.parent:
            tree_root_class = ' tree-root'

        r += (
            '<span id="page_marker-%d" class="page_marker%s%s"'
            ' style="width: %dpx;">&nbsp;</span>&nbsp;') % (
            item.pk,
            changeable_class,
            tree_root_class,
            14 + getattr(item, mptt_opts.level_attr) * 18)

#        r += '<span tabindex="0">'
        if hasattr(item, 'short_title') and callable(item.short_title):
            r += escape(item.short_title())
        else:
            r += escape('%s' % item)
#        r += '</span>'
        return mark_safe(r)
    indented_short_title.short_description = _('title')

    def _collect_editable_booleans(self):
        """
        Collect all fields marked as editable booleans. We do not
        want the user to be able to edit arbitrary fields by crafting
        an AJAX request by hand.
        """
        if hasattr(self, '_ajax_editable_booleans'):
            return

        self._ajax_editable_booleans = {}

        for field in self.list_display:
            # The ajax_editable_boolean return value has to be assigned
            # to the ModelAdmin class
            try:
                item = getattr(self.__class__, field)
            except (AttributeError, TypeError):
                continue

            attr = getattr(item, 'editable_boolean_field', None)
            if attr:
                if hasattr(item, 'editable_boolean_result'):
                    result_func = item.editable_boolean_result
                else:
                    def _fn(attr):
                        return lambda self, instance: [
                            ajax_editable_boolean_cell(instance, attr)]
                    result_func = _fn(attr)
                self._ajax_editable_booleans[attr] = result_func

    def _toggle_boolean(self, request):
        """
        Handle an AJAX toggle_boolean request
        """
        try:
            item_id = int(request.POST.get('item_id', None))
            attr = str(request.POST.get('attr', None))
        except:
            return HttpResponseBadRequest("Malformed request")

        if not request.user.is_staff:
            logger.warning(
                "Denied AJAX request by non-staff \"%s\" to toggle boolean"
                " %s for object #%s", request.user, attr, item_id)
            return HttpResponseForbidden(
                _("You do not have permission to modify this object"))

        self._collect_editable_booleans()

        if attr not in self._ajax_editable_booleans:
            return HttpResponseBadRequest("not a valid attribute %s" % attr)

        try:
            obj = self.model._default_manager.get(pk=item_id)
        except self.model.DoesNotExist:
            return HttpResponseNotFound("Object does not exist")

        if not self.has_change_permission(request, obj=obj):
            logger.warning(
                "Denied AJAX request by \"%s\" to toggle boolean %s for"
                " object %s", request.user, attr, item_id)
            return HttpResponseForbidden(
                _("You do not have permission to modify this object"))

        new_state = not getattr(obj, attr)
        logger.info(
            "Toggle %s on #%d %s to %s by \"%s\"",
            attr, obj.pk, obj, "on" if new_state else "off", request.user)

        try:
            before_data = self._ajax_editable_booleans[attr](self, obj)

            setattr(obj, attr, new_state)
            obj.save()

            # Construct html snippets to send back to client for status update
            data = self._ajax_editable_booleans[attr](self, obj)

        except Exception:
            logger.exception(
                "Unhandled exception while toggling %s on %s", attr, obj)
            return HttpResponseServerError(
                "Unable to toggle %s on %s" % (attr, obj))

        # Weed out unchanged cells to keep the updates small. This assumes
        # that the order a possible get_descendents() returns does not change
        # before and after toggling this attribute. Unlikely, but still...
        return HttpResponse(
            json.dumps([b for a, b in zip(before_data, data) if a != b]),
            content_type="application/json")

    def get_changelist(self, request, **kwargs):
        return ChangeList

    def changelist_view(self, request, extra_context=None, *args, **kwargs):
        """
        Handle the changelist view, the django view for the model instances
        change list/actions page.
        """

        if 'actions_column' not in self.list_display:
            self.list_display.append('actions_column')

        # handle common AJAX requests
        if request.is_ajax():
            cmd = request.POST.get('__cmd')
            if cmd == 'toggle_boolean':
                return self._toggle_boolean(request)
            elif cmd == 'move_node':
                return self._move_node(request)

            return HttpResponseBadRequest('Oops. AJAX request not understood.')

        extra_context = extra_context or {}
        extra_context['tree_structure'] = mark_safe(
            json.dumps(_build_tree_structure(self.get_queryset(request))))
        extra_context['node_levels'] = mark_safe(json.dumps(
            dict(self.get_queryset(request).order_by().values_list(
                'pk', self.model._mptt_meta.level_attr
            ))
        ))

        return super(TreeEditor, self).changelist_view(
            request, extra_context, *args, **kwargs)

    def has_add_permission(self, request, obj=None):
        """
        Implement a lookup for object level permissions. Basically the same as
        ModelAdmin.has_add_permission, but also passes the obj parameter in.
        """
        perm = self.object_add_permission
        if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
            r = request.user.has_perm(perm, obj)
        else:
            r = request.user.has_perm(perm)

        return r and super(TreeEditor, self).has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """
        Implement a lookup for object level permissions. Basically the same as
        ModelAdmin.has_change_permission, but also passes the obj parameter in.
        """
        perm = self.object_change_permission
        if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
            r = request.user.has_perm(perm, obj)
        else:
            r = request.user.has_perm(perm)

        return r and super(TreeEditor, self).has_change_permission(
            request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Implement a lookup for object level permissions. Basically the same as
        ModelAdmin.has_delete_permission, but also passes the obj parameter in.
        """
        perm = self.object_delete_permission
        if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
            r = request.user.has_perm(perm, obj)
        else:
            r = request.user.has_perm(perm)

        return r and super(TreeEditor, self).has_delete_permission(
            request, obj)

    def _move_node(self, request):
        if hasattr(self.model.objects, 'move_node'):
            tree_manager = self.model.objects
        else:
            tree_manager = self.model._tree_manager

        queryset = self.get_queryset(request)
        cut_item = queryset.get(pk=request.POST.get('cut_item'))
        pasted_on = queryset.get(pk=request.POST.get('pasted_on'))
        position = request.POST.get('position')

        if not self.has_change_permission(request, cut_item):
            self.message_user(request, _('No permission'))
            return HttpResponse('FAIL')

        if position in ('last-child', 'left', 'right'):
            try:
                tree_manager.move_node(cut_item, pasted_on, position)
            except InvalidMove as e:
                self.message_user(request, '%s' % e)
                return HttpResponse('FAIL')

            # Ensure that model save methods have been run (required to
            # update Page._cached_url values, might also be helpful for other
            # models inheriting MPTTModel)
            for item in queryset.filter(id__in=(cut_item.pk, pasted_on.pk)):
                item.save()

            self.message_user(
                request,
                ugettext('%s has been moved to a new position.') % cut_item)
            return HttpResponse('OK')

        self.message_user(request, _('Did not understand moving instruction.'))
        return HttpResponse('FAIL')

    def _actions_column(self, instance):
        if self.changeable(instance):
            return ['<div class="drag_handle"></div>']
        return []

    def actions_column(self, instance):
        return mark_safe(' '.join(self._actions_column(instance)))
    actions_column.short_description = _('actions')

    def delete_selected_tree(self, modeladmin, request, queryset):
        """
        Deletes multiple instances and makes sure the MPTT fields get
        recalculated properly. (Because merely doing a bulk delete doesn't
        trigger the post_delete hooks.)
        """
        # If this is True, the confirmation page has been displayed
        if request.POST.get('post'):
            n = 0
            # TODO: The disable_mptt_updates / rebuild is a work around
            # for what seems to be a mptt problem when deleting items
            # in a loop. Revisit this, there should be a better solution.
            with queryset.model.objects.disable_mptt_updates():
                for obj in queryset:
                    if self.has_delete_permission(request, obj):
                        obj.delete()
                        n += 1
                        obj_display = force_text(obj)
                        self.log_deletion(request, obj, obj_display)
                    else:
                        logger.warning(
                            "Denied delete request by \"%s\" for object #%s",
                            request.user, obj.id)
            if n > 0:
                queryset.model.objects.rebuild()
            self.message_user(
                request,
                _("Successfully deleted %(count)d items.") % {"count": n})
            # Return None to display the change list page again
            return None
        else:
            # (ab)using the built-in action to display the confirmation page
            return delete_selected(self, request, queryset)

    def get_actions(self, request):
        actions = super(TreeEditor, self).get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'] = (
                self.delete_selected_tree,
                'delete_selected',
                _("Delete selected %(verbose_name_plural)s"))
        return actions

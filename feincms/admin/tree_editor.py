# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import json
import logging

from django.conf import settings as django_settings
from django.contrib import admin
from django.contrib.admin.views import main
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext

from mptt.exceptions import InvalidMove
from mptt.forms import MPTTAdminForm

from feincms import settings


# ------------------------------------------------------------------------
def django_boolean_icon(field_val, alt_text=None, title=None):
    """
    Return HTML code for a nice representation of true/false.
    """

    # Origin: contrib/admin/templatetags/admin_list.py
    BOOLEAN_MAPPING = { True: 'yes', False: 'no', None: 'unknown' }
    alt_text = alt_text or BOOLEAN_MAPPING[field_val]
    if title is not None:
        title = 'title="%s" ' % title
    else:
        title = ''
    return mark_safe(u'<img src="%sfeincms/img/icon-%s.gif" alt="%s" %s/>' %
            (django_settings.STATIC_URL, BOOLEAN_MAPPING[field_val], alt_text, title))


def _build_tree_structure(cls):
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
    all_nodes = { }

    mptt_opts = cls._mptt_meta

    for p_id, parent_id in cls.objects.order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr).values_list("pk", "%s_id" % mptt_opts.parent_attr):
        all_nodes[p_id] = []

        if parent_id:
            if not all_nodes.has_key(parent_id):
                # This happens very rarely, but protect against parents that
                # we have yet to iteratove over.
                all_nodes[parent_id] = []
            all_nodes[parent_id].append(p_id)

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
        text = '&nbsp;(%s)' % unicode(text)

    if override is not None:
        a = [ django_boolean_icon(override, text), text ]
    else:
        value = getattr(item, attr)
        a = [
              '<input type="checkbox"',
              value and ' checked="checked"' or '',
              ' onclick="return inplace_toggle_boolean(%d, \'%s\')"' % (item.pk, attr),
              ' />',
              text,
            ]

    a.insert(0, '<div id="wrap_%s_%d">' % ( attr, item.pk ))
    a.append('</div>')
    return unicode(''.join(a))

# ------------------------------------------------------------------------
def ajax_editable_boolean(attr, short_description):
    """
    Convenience function: Assign the return value of this method to a variable
    of your ModelAdmin class and put the variable name into list_display.

    Example::

        class MyTreeEditor(TreeEditor):
            list_display = ('__unicode__', 'active_toggle')

            active_toggle = ajax_editable_boolean('active', _('is active'))
    """
    def _fn(self, item):
        return ajax_editable_boolean_cell(item, attr)
    _fn.allow_tags = True
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

    def get_query_set(self, *args, **kwargs):
        mptt_opts = self.model._mptt_meta
        return super(ChangeList, self).get_query_set(*args, **kwargs).order_by(mptt_opts.tree_id_attr, mptt_opts.left_attr)

    def get_results(self, request):
        mptt_opts = self.model._mptt_meta
        if settings.FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS:
            clauses = [Q(**{
                mptt_opts.tree_id_attr: tree_id,
                mptt_opts.left_attr + '__lte': lft,
                mptt_opts.right_attr + '__gte': rght,
                }
                ) for lft, rght, tree_id in \
                    self.query_set.values_list(mptt_opts.left_attr, mptt_opts.right_attr, mptt_opts.tree_id_attr)]
            if clauses:
                self.query_set = self.model._default_manager.filter(reduce(lambda p, q: p|q, clauses))

        super(ChangeList, self).get_results(request)

        for item in self.result_list:
            if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
                item.feincms_editable = self.model_admin.has_change_permission(request, item)
            else:
                item.feincms_editable = True

# ------------------------------------------------------------------------
# MARK: -
# ------------------------------------------------------------------------

class TreeEditor(admin.ModelAdmin):
    """
    The ``TreeEditor`` modifies the standard Django administration change list
    to a drag-drop enabled interface for django-mptt_-managed Django models.

    .. _django-mptt: https://github.com/django-mptt/django-mptt/
    """

    form = MPTTAdminForm

    if settings.FEINCMS_TREE_EDITOR_INCLUDE_ANCESTORS:
        # Make sure that no pagination is displayed. Slicing is disabled anyway,
        # therefore this value does not have an influence on the queryset
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
            'admin/feincms/%s/%s/tree_editor.html' % (opts.app_label, opts.object_name.lower()),
            'admin/feincms/%s/tree_editor.html' % opts.app_label,
            'admin/feincms/tree_editor.html',
            ]

    def editable(self, item):
        return getattr(item, 'feincms_editable', True)

    def indented_short_title(self, item):
        """
        Generate a short title for an object, indent it depending on
        the object's depth in the hierarchy.
        """
        mptt_opts = item._mptt_meta
        r = ''
        if hasattr(item, 'get_absolute_url'):
            r = '<input type="hidden" class="medialibrary_file_path" value="%s" id="_refkey_%d" />' % (
                        item.get_absolute_url(),
                        item.pk
                      )

        editable_class = ''
        if not getattr(item, 'feincms_editable', True):
            editable_class = ' tree-item-not-editable'

        r += '<span id="page_marker-%d" class="page_marker%s" style="width: %dpx;">&nbsp;</span>&nbsp;' % (
                item.pk, editable_class, 14+getattr(item, mptt_opts.level_attr)*18)
#        r += '<span tabindex="0">'
        if hasattr(item, 'short_title'):
            r += item.short_title()
        else:
            r += unicode(item)
#        r += '</span>'
        return mark_safe(r)
    indented_short_title.short_description = _('title')
    indented_short_title.allow_tags = True

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
                        return lambda self, instance: [ajax_editable_boolean_cell(instance, attr)]
                    result_func = _fn(attr)
                self._ajax_editable_booleans[attr] = result_func

    def _refresh_changelist_caches(self):
        """
        Refresh information used to show the changelist tree structure such as
        inherited active/inactive states etc.

        XXX: This is somewhat hacky, but since it's an internal method, so be it.
        """

        pass

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
            logging.warning("Denied AJAX request by non-staff %s to toggle boolean %s for object #%s", request.user, attr, item_id)
            return HttpResponseForbidden("You do not have permission to access this object")

        self._collect_editable_booleans()

        if not self._ajax_editable_booleans.has_key(attr):
            return HttpResponseBadRequest("not a valid attribute %s" % attr)

        try:
            obj = self.model._default_manager.get(pk=item_id)
        except self.model.DoesNotExist:
            return HttpResponseNotFound("Object does not exist")

        if not self.has_change_permission(request, obj=obj):
            logging.warning("Denied AJAX request by %s to toggle boolean %s for object %s", request.user, attr, item_id)
            return HttpResponseForbidden("You do not have permission to access this object")

        logging.info("Processing request by %s to toggle %s on %s", request.user, attr, obj)

        try:
            before_data = self._ajax_editable_booleans[attr](self, obj)

            setattr(obj, attr, not getattr(obj, attr))
            obj.save()

            self._refresh_changelist_caches() # ???: Perhaps better a post_save signal?

            # Construct html snippets to send back to client for status update
            data = self._ajax_editable_booleans[attr](self, obj)

        except Exception:
            logging.exception("Unhandled exception while toggling %s on %s", attr, obj)
            return HttpResponseServerError("Unable to toggle %s on %s" % (attr, obj))

        # Weed out unchanged cells to keep the updates small. This assumes
        # that the order a possible get_descendents() returns does not change
        # before and after toggling this attribute. Unlikely, but still...
        d = []
        for a, b in zip(before_data, data):
            if a != b:
                d.append(b)

        # TODO: Shorter: [ y for x,y in zip(a,b) if x!=y ]
        return HttpResponse(json.dumps(d), mimetype="application/json")

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
            else:
                return HttpResponseBadRequest('Oops. AJAX request not understood.')

        self._refresh_changelist_caches()

        extra_context = extra_context or {}
        extra_context['tree_structure'] = mark_safe(json.dumps(
                                                    _build_tree_structure(self.model)))

        return super(TreeEditor, self).changelist_view(request, extra_context, *args, **kwargs)

    def has_change_permission(self, request, obj=None):
        """
        Implement a lookup for object level permissions. Basically the same as
        ModelAdmin.has_change_permission, but also passes the obj parameter in.
        """
        if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
            opts = self.opts
            r = request.user.has_perm(opts.app_label + '.' + opts.get_change_permission(), obj)
        else:
            r = True

        return r and super(TreeEditor, self).has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        Implement a lookup for object level permissions. Basically the same as
        ModelAdmin.has_delete_permission, but also passes the obj parameter in.
        """
        if settings.FEINCMS_TREE_EDITOR_OBJECT_PERMISSIONS:
            opts = self.opts
            r = request.user.has_perm(opts.app_label + '.' + opts.get_delete_permission(), obj)
        else:
            r = True

        return r and super(TreeEditor, self).has_delete_permission(request, obj)

    def _move_node(self, request):
        if hasattr(self.model.objects, 'move_node'):
            tree_manager = self.model.objects
        else:
            tree_manager = self.model._tree_manager

        cut_item = tree_manager.get(pk=request.POST.get('cut_item'))
        pasted_on = tree_manager.get(pk=request.POST.get('pasted_on'))
        position = request.POST.get('position')

        if position in ('last-child', 'left'):
            try:
                tree_manager.move_node(cut_item, pasted_on, position)
            except InvalidMove, e:
                self.message_user(request, unicode(e))
                return HttpResponse('FAIL')

            # Ensure that model save has been run
            cut_item = self.model.objects.get(pk=cut_item.pk)
            cut_item.save()

            self.message_user(request, ugettext('%s has been moved to a new position.') %
                cut_item)
            return HttpResponse('OK')

        self.message_user(request, ugettext('Did not understand moving instruction.'))
        return HttpResponse('FAIL')

    def _actions_column(self, instance):
        return ['<div class="drag_handle"></div>',]

    def actions_column(self, instance):
        return u' '.join(self._actions_column(instance))
    actions_column.allow_tags = True
    actions_column.short_description = _('actions')

    def delete_selected_tree(self, modeladmin, request, queryset):
        """
        Deletes multiple instances and makes sure the MPTT fields get
        recalculated properly.  (Because merely doing a bulk delete doesn't
        trigger the post_delete hooks.)
        """
        n = 0
        for obj in queryset:
            obj.delete()
            n += 1
        self.message_user(request, _("Successfully deleted %s items.") % n)

    def get_actions(self, request):
        actions = super(TreeEditor, self).get_actions(request)
        if 'delete_selected' in actions:
            actions['delete_selected'] = (
                self.delete_selected_tree,
                'delete_selected',
                _("Delete selected %(verbose_name_plural)s"))
        return actions

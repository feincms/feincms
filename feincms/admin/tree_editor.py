from django import template
from django.conf import settings as django_settings
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.util import unquote
from django.db import connection, models
from django.http import HttpResponseRedirect, HttpResponse, Http404, \
    HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils import dateformat, simplejson
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import get_date_formats, ugettext as _

from feincms import settings


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
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" %s/>' %
            (django_settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], alt_text, title))


class TreeEditor(admin.ModelAdmin):
    actions = None # TreeEditor does not like the checkbox column

    def changelist_view(self, request, extra_context=None):
        from django.contrib.admin.views.main import ChangeList, ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label

        if not self.has_change_permission(request, None):
            raise PermissionDenied
        try:
            if settings.DJANGO10_COMPAT:
                self.changelist = ChangeList(request, self.model, self.list_display,
                    self.list_display_links, self.list_filter, self.date_hierarchy,
                    self.search_fields, self.list_select_related, self.list_per_page,
                    self)
            else:
                self.changelist = ChangeList(request, self.model, self.list_display,
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

        # handle AJAX requests
        if request.is_ajax():
            cmd = request.POST.get('__cmd')
            if cmd == 'save_tree':
                return self._save_tree(request)
            elif cmd == 'delete_item':
                return self._delete_item(request)
            elif cmd == 'toggle_boolean':
                return self._toggle_boolean(request)

            return HttpResponse('Oops. AJAX request not understood.')

        # XXX Hack alarm!
        # if actions is defined, Django adds a new field to list_display, action_checkbox. The
        # TreeEditor cannot cope with this (yet), so we remove it by hand.
        if 'action_checkbox' in self.changelist.list_display:
            self.changelist.list_display.remove('action_checkbox')

        context = {
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': settings.FEINCMS_ADMIN_MEDIA_HOTLINKING,
            'title': self.changelist.title,
            'is_popup': self.changelist.is_popup,
            'cl': self.changelist,
            'has_add_permission': self.has_add_permission(request),
            'root_path': self.admin_site.root_path,
            'app_label': app_label,
            'object_list': self.model._tree_manager.all(),
            'tree_editor': self,

            'result_headers': list(admin_list.result_headers(self.changelist)),
        }
        context.update(extra_context or {})
        return render_to_response([
            'admin/feincms/%s/%s/tree_editor.html' % (app_label, opts.object_name.lower()),
            'admin/feincms/%s/tree_editor.html' % app_label,
            'admin/feincms/tree_editor.html',
            ], context, context_instance=template.RequestContext(request))

    def object_list(self):
        first_field = self.changelist.list_display[0]

        ancestors = []

        for item in self.model._tree_manager.all().select_related():
            # The first field is handled separately, because we have to add a bit more HTML
            # code to the table cell for the expanders.
            first = getattr(item, first_field)
            if callable(first):
                first = first()

            yield item, first, list(admin_list.items_for_result(self.changelist, item, None))[1:]

    def _save_tree(self, request):
        """
        The incoming data is structured as a list of lists. Every item has
        a list entry holding the primary key, the primary key of its parent
        (or anything evaluating to false in a boolean context if it is a
        toplevel entry) and a flag indicating whether the item has children
        or not.
        """

        itemtree = simplejson.loads(request.POST['tree'])

        tree_id = 0
        parents = []

        # map item primary keys to data array indices
        node_indices = {}

        # Data is a list of lists holding the data which is used to update
        # the database at the end of this view.
        # The sublist have the following structure:
        # [tree_id, parent_id, left, right, level, item_id]
        data = []

        def incrementer(start):
            # Returns an ever-increasing stream of numbers. The starting
            # point can be freely defined.
            while True:
                yield start
                start += 1

        left = incrementer(0)

        for item_id, parent_id, has_children in itemtree:
            node_indices[item_id] = len(node_indices)

            if parent_id in parents:
                # We are processing another child element. However, we might
                # be processing an item that's further up the tree than the
                # previous. Walk up the tree until the parent_id of the current
                # item is the last element in the parents list. 
                for i in range(len(parents) - parents.index(parent_id) - 1):
                    data[node_indices[parents.pop()]][3] = left.next()
            elif not parent_id:
                # We are processing a top-level item. Completely drain the
                # parents list, and start a new tree.
                while parents:
                    data[node_indices[parents.pop()]][3] = left.next()
                left = incrementer(0)
                tree_id += 1

            data.append([
                tree_id,
                parent_id and parent_id or None,
                left.next(),
                0, # The "right" value can only be determined when walking
                   # back up the tree, not now. 
                len(parents),
                item_id,
                ])

            if has_children:
                parents.append(item_id)
            else:
                # Finalize the current element (assign the "right" value to
                # the last element from data, that is, the current item.)
                data[-1][3] = left.next()

        while parents:
            # Completely drain the parents list again. There will often be a
            # couple of "right" values that still need to be assigned.
            data[node_indices[parents.pop()]][3] = left.next()

        # 0 = tree_id, 1 = parent_id, 2 = left, 3 = right, 4 = level, 5 = item_id
        sql = "UPDATE %s SET %s=%%s, %s_id=%%s, %s=%%s, %s=%%s, %s=%%s WHERE %s=%%s" % (
            self.model._meta.db_table,
            self.model._meta.tree_id_attr,
            self.model._meta.parent_attr,
            self.model._meta.left_attr,
            self.model._meta.right_attr,
            self.model._meta.level_attr,
            self.model._meta.pk.column)

        connection.cursor().executemany(sql, data)

        # call save on all toplevel objects, thereby ensuring that caches are
        # regenerated (if they exist)
        # XXX This is currently only really needed for the page module. Maybe we
        # should use a signal for this?
        # NOTE! If you remove these lines, be sure to make Django commit the
        # current transaction if we have one -- Django won't do it when we've
        # manipulated the DB only directly using cursors.
        # --> transaction.commit_unless_managed()
        for item in self.model._tree_manager.root_nodes():
            item.save()

        return HttpResponse("OK", mimetype="text/plain")

    def _delete_item(self, request):
        item_id = request.POST['item_id']
        try:
            obj = self.model._default_manager.get(pk=unquote(item_id))
            obj.delete()
        except Exception, e:
            return HttpResponse("FAILED " + unicode(e), mimetype="text/plain")

        return HttpResponse("OK", mimetype="text/plain")

    def _toggle_boolean(self, request):
        if not hasattr(self, '_ajax_editable_booleans'):
            # Collect all fields marked as editable booleans. We do not
            # want the user to be able to edit arbitrary fields by crafting
            # an AJAX request by hand.
            self._ajax_editable_booleans = []

            for field in self.list_display:
                # The ajax_editable_boolean return value has to be assigned
                # to the ModelAdmin class
                item = getattr(self.__class__, field, None)
                if not item:
                    continue

                attr = getattr(item, 'editable_boolean_field', None)
                if attr:
                    self._ajax_editable_booleans.append(attr)

        item_id = request.POST.get('item_id')
        attr = request.POST.get('attr')

        if attr not in self._ajax_editable_booleans:
            return HttpResponseBadRequest()

        try:
            obj = self.model._default_manager.get(pk=unquote(item_id))
            setattr(obj, attr, not getattr(obj, attr))
            obj.save()
        except Exception, e:
            return HttpResponse("FAILED " + unicode(e), mimetype="text/plain")

        data = [(obj.id, ajax_editable_boolean_cell(obj, attr))]

        # TODO descend recursively, sometimes (f.e. for Page.active)

        return HttpResponse(simplejson.dumps(data), mimetype="application/json")


def ajax_editable_boolean_cell(item, attr):
    return '<a class="attr_%s" href="#" onclick="return toggle_boolean(this, \'%s\')">%s</a>' % (
        attr, attr, django_boolean_icon(getattr(item, attr), 'toggle %s' % attr))


def ajax_editable_boolean(attr, short_description):
    """
    Assign the return value of this method to a variable of your ModelAdmin
    subclass of TreeEditor and put the variable name into list_display.

    Example:
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

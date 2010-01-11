from django import template
from django.conf import settings as django_settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils.text import capfirst

from feincms import settings


class SplitPaneEditor(admin.ModelAdmin):

    # This can be replaced dynamically with another condition if the need
    # should arise. Using AJAX if the tree node count exceeds 25 tries to
    # be a sane default only, nothing more.
    delayed_tree_loading = lambda self: self.model._tree_manager.count() > 25

    def changelist_view(self, request, extra_context=None):
        if 'mptt' not in django_settings.INSTALLED_APPS:
            # mptt_tags is needed to build the nested tree for the tree view
            raise ImproperlyConfigured, 'You have to add \'mptt\' to INSTALLED_APPS to use the SplitPaneEditor'

        if not self.has_change_permission(request, None):
            raise PermissionDenied

        if request.is_ajax():
            cmd = request.REQUEST.get('__cmd')
            if cmd == 'move_node':
                return self._move_node(request)
            elif cmd == 'subtree':
                return self._subtree_view(request)

            return HttpResponseBadRequest('Oops. AJAX request not understood.')

        if '_tree' in request.GET:
            # Left frame
            return self._tree_view(request)
        elif '_blank' in request.GET:
            # Default content for right frame (if the user is not editing
            # any items currently)
            return self._blank_view(request)
        elif 'pop' in request.GET:
            # Delegate to default implementation for raw_id_fields etc
            return super(SplitPaneEditor, self).changelist_view(request, extra_context)

        return render_to_response('admin/feincms/splitpane_editor.html')

    def _tree_view(self, request):
        # XXX the default manager isn't guaranteed to have a method
        # named "active" at all...
        try:
            inactive_nodes = self.model._default_manager.exclude(
                id__in=self.model._default_manager.active()).values_list('id', flat=True)
        except AttributeError:
            inactive_nodes = []

        opts = self.model._meta

        context = {
            'opts': opts,
            'root_path': self.admin_site.root_path,
            'inactive_nodes': ', '.join('#item%d' % i for i in inactive_nodes),
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_TREE_DRAG_AND_DROP': settings.FEINCMS_ADMIN_TREE_DRAG_AND_DROP
            }

        if self.delayed_tree_loading():
            context['object_list'] = self.model._tree_manager.root_nodes()
        else:
            context['object_list'] = self.model._tree_manager.all()
            context['full_object_list'] = True

        return render_to_response([
            'admin/feincms/%s/%s/splitpane_editor_tree.html' % (opts.app_label, opts.object_name.lower()),
            'admin/feincms/%s/splitpane_editor_tree.html' % opts.app_label,
            'admin/feincms/splitpane_editor_tree.html',
            ], context, context_instance=template.RequestContext(request))

    def _subtree_view(self, request):
        parent = self.model._default_manager.get(pk=request.GET.get('parent'))
        return render_to_response('admin/feincms/splitpane_editor_tree_subtree.html', {
                                  'object_list': parent.get_children(),
                                   })

    def _blank_view(self, request):
        opts = self.model._meta

        return render_to_response('admin/feincms/splitpane_editor_blank.html', {
            'has_add_permission': self.has_add_permission(request),
            'root_path': self.admin_site.root_path,
            'title': capfirst(opts.verbose_name_plural),
            'opts': opts,
            }, context_instance=template.RequestContext(request))

    def _move_node(self, request):
        destination_id = int(request.POST.get('destination'))
        source_id = int(request.POST.get('source'))
        position = int(request.POST.get('position'))

        if destination_id == 0:
            siblings = self.model._tree_manager.root_nodes()
        else:
            parent = self.model._tree_manager.get(pk=destination_id)
            siblings = parent.get_children()

        source = self.model._tree_manager.get(pk=source_id)

        if siblings.count() == 0:
            # This can only happen when destination != 0
            # Insert dragged element as new (and only) child
            self.model._tree_manager.move_node(source, parent, 'last-child')
        elif position == 0:
            sibling = siblings[0]
            if sibling != source:
                # Only do something if item was not dragged to the same place
                # as it was before
                self.model._tree_manager.move_node(source, siblings[0], 'left')
        else:
            sibling = siblings[position - 1]
            if source in siblings[:position]:
                # The item is a direct sibling of its former position. If the
                # item's place was somewhere before its new place, we have to
                # adjust the position slightly
                self.model._tree_manager.move_node(source, siblings[position], 'right')
            else:
                # Otherwise, add it to the right of the target node. This
                # works for last childs too
                self.model._tree_manager.move_node(source, siblings[position - 1], 'right')

        # Ensure that model save has been run
        source = self.model._tree_manager.get(pk=source_id)
        source.save()

        return HttpResponse('OK')

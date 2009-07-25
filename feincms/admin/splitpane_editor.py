from django import template
from django.conf import settings as django_settings
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response
from django.utils import simplejson
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from feincms import settings


class SplitPaneEditor(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        if 'mptt' not in django_settings.INSTALLED_APPS:
            raise ImproperlyConfigured, 'You have to add \'mptt\' to INSTALLED_APPS to use the SplitPaneEditor'

        if not self.has_change_permission(request, None):
            raise PermissionDenied

        if request.is_ajax():
            return HttpResponse('hello world')

        if '_tree' in request.GET:
            return self._tree_view(request)

        if '_blank' in request.GET:
            return self._blank_view(request)

        if 'pop' in request.GET:
            # Delegate to default implementation for raw_id_fields etc
            return super(SplitPaneEditor, self).changelist_view(request, extra_context)

        return render_to_response('admin/feincms/splitpane_editor.html')

    def _tree_view(self, request):
        return render_to_response('admin/feincms/splitpane_editor_tree.html', {
            'object_list': self.model._tree_manager.all(),
            'opts': self.model._meta,
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            }, context_instance=template.RequestContext(request))

    def _blank_view(self, request):
        from django.contrib.admin.views.main import ChangeList, ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label

        return render_to_response('admin/feincms/splitpane_editor_blank.html', {
            'title': opts.verbose_name_plural,
            'has_add_permission': self.has_add_permission(request),
            'root_path': self.admin_site.root_path,
            'opts': opts,
            }, context_instance=template.RequestContext(request))

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

        if 'tree' in request.GET:
            return self._tree_view(request)

        return render_to_response('admin/feincms/splitpane_editor.html')

    def _tree_view(self, request):
        return render_to_response('admin/feincms/splitpane_editor_tree.html', {
            'object_list': self.model._tree_manager.all(),
            'FEINCMS_ADMIN_MEDIA': settings.FEINCMS_ADMIN_MEDIA,
            }, context_instance=template.RequestContext(request))

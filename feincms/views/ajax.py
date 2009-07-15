# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------

from django.contrib.auth.decorators  import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponse
from django.utils.safestring import mark_safe

from feincms.module.page.models import Page
from feincms.module import django_boolean_icon

# ------------------------------------------------------------------------
@login_required
def toggle(request):
    page_id = int(request.POST['id'])
    attr    = str(request.POST['attr'])
    path    = request.META['PATH_INFO']

    # Safety checks
    if request.POST and request.is_ajax() and \
                        attr in ('in_navigation', ):
        page = get_object_or_404(Page, pk=page_id)
        v = not getattr(page, attr)
        setattr(page, attr, v)
        page.save()

        return HttpResponse(django_boolean_icon(v), 'text/html')

    raise HttpResponseBadRequest

# ------------------------------------------------------------------------

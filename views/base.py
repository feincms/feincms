from django.shortcuts import render_to_response
from django.template import RequestContext

from feincms.models import Page


def handler(request, path):
    page = Page.objects.page_for_path_or_404(path)

    return render_to_response(page.template.path, {
        'page': page,
        }, context_instance=RequestContext(request))


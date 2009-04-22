from django.shortcuts import render_to_response
from django.template import RequestContext

from feincms.module.page.models import Page


def render_to_response_best_match(request, template_name, dictionary=None):
    dictionary = dictionary or {}
    dictionary['feincms_page'] = Page.objects.best_match_for_request(request)

    return render_to_response(template_name, dictionary,
        context_instance=RequestContext(request))


from __future__ import absolute_import, unicode_literals

from django.shortcuts import render

from feincms.module.page.models import Page


def render_to_response_best_match(request, template_name, dictionary=None):
    """
    ``render_to_response`` wrapper using best match for the current page.
    """

    dictionary = dictionary or {}
    dictionary['feincms_page'] = Page.objects.best_match_for_request(request)

    return render(request, template_name, dictionary)

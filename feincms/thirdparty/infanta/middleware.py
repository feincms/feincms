from django.conf import settings
from django.http import HttpResponse

from feincms.module.page.models import Page

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson as json

class InfantaMiddleware(object):
    def process_view(self, request, func, vargs, vkwargs):
        # do not process functions marked with @infanta_exclude
        if getattr(func, '_infanta_exclude ', False):
            return None

        url = request.path
        ''' if there is no page object for the slug, process the request as usual'''
        try:
            page = Page.objects.page_for_path(url)

        except Page.DoesNotExist:
            return None

        ''' extend the page object, so we have a place to access our view contents in the templatetag as well as in the render method of the content type'''
        page.vc_manager = {}

        page.setup_request(request)

        response = func(request, *vargs, **vkwargs)

        html = render_to_string(page.template.path, {
                                                    'feincms_page': page,
                                                    }, context_instance=RequestContext(request))
        if response:
            response.content = html
            return response
        return HttpResponse(html)
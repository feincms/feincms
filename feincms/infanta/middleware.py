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
            return

        page = Page.objects.best_match_for_path(request.path, raise404=True)

        '''
        extend the page object, so we have an attribute to access 
        our view contents in the templatetag  as well as in the render method 
        of the content type
        '''
        page.vc_manager = {}

        # run request processors and return short-circuit the response handling
        # if a request processor returned a response.
        response = page.setup_request(request)
        if response:
            return response

        response = func(request, *vargs, **vkwargs)

        # The {% box %} template tag has captured the content of the third-party
        # application and should have stored it inside the view content manager.
        # We do not need to pass the content explicitly therefore.
        html = render_to_string(page.template.path, {
                                                    'feincms_page': page,
                                                    }, context_instance=RequestContext(request))
        if response:
            response.content = html
            return response
        return HttpResponse(html)
from feincms import settings
from feincms.module.page.models import Page


class InfantaMiddleware(object):
    def process_view(self, request, func, vargs, vkwargs):
        # do not process functions marked with @infanta_exclude
        if getattr(func, '_infanta_exclude ', False):
            return

        for url in settings.INFANTA_EXCLUDE_URLS:
            if request.path.startswith(url):
                return

        page = Page.objects.best_match_for_path(request.path)

        if not page:
        	return

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

        return(func(request, *vargs, **vkwargs))


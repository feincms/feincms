from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.cache import add_never_cache_headers

from feincms import settings
from feincms.module.page.models import Page


class Handler(object):
    """
    This is the legacy handler for feincms page content.

    It isn't a class-based-view like those in Django's generic view framework.
    State should not be stored on the ``Handler`` class, because of thread-safety
    and cross polination issues.
    """

    def __call__(self, request, path=None):
        return self.build_response(request,
            Page.objects.best_match_for_path(path or request.path, raise404=True))

    def build_response(self, request, page):
        """
        Calls `prepare`, `render` and `finalize`, in this order.
        """

        response = self.prepare(request, page)
        if response:
            return response

        response = self.render(request, page)
        return self.finalize(request, response, page)

    def prepare(self, request, page):
        """
        Prepare / pre-process content types. If this method returns anything,
        it is treated as a ``HttpResponse`` and handed back to the visitor.
        """

        response = page.setup_request(request)
        if response:
            return response

        http404 = None     # store eventual Http404 exceptions for re-raising,
                           # if no content type wants to handle the current request
        successful = False # did any content type successfully end processing?

        for content in page.content.all_of_type(tuple(page._feincms_content_types_with_process)):
            try:
                r = content.process(request)
                if r in (True, False):
                    successful = r
                elif r:
                    return r
            except Http404, e:
                http404 = e

        if not successful:
            if http404:
                # re-raise stored Http404 exception
                raise http404

            if not settings.FEINCMS_ALLOW_EXTRA_PATH and \
                    request._feincms_extra_context['extra_path'] != '/':
                raise Http404

    def render(self, request, page):
        """
        The render step. Must return a HttpResponse.
        """

        # This facility can be used by request processors to add values
        # to the context.
        context = request._feincms_extra_context
        context['feincms_page'] = page

        return render_to_response(page.template.path,
            context_instance=RequestContext(request, context))

    def finalize(self, request, response, page):
        """
        Runs finalize() on content types having such a method, adds headers and
        returns the final response.
        """

        for content in page.content.all_of_type(tuple(page._feincms_content_types_with_finalize)):
            r = content.finalize(request, response)
            if r:
                return r

        page.finalize_response(request, response)

        # Add never cache headers in case frontend editing is active
        if hasattr(request, "session") and request.session.get('frontend_editing', False):
            add_never_cache_headers(response)

        return response

    @property
    def __name__(self):
        """
        Dummy property to make this handler behave like a normal function.
        This property is used by django-debug-toolbar
        """
        return self.__class__.__name__

#: Default handler
handler = Handler()

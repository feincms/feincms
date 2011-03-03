from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.cache import add_never_cache_headers

from feincms.module.page.models import Page


class Handler(object):
    """
    This is the default handler for feincms page content.
    """

    def __call__(self, request, path=None):
        return self.build_response(request,
            Page.objects.page_for_path_or_404(path or request.path))

    def build_response(self, request, page):
        response = self.prepare(request, page)
        if response:
            return response

        response = self.render(request, page)
        return self.finalize(request, response, page)

    def prepare(self, request, page):
        """
        Prepare / pre-process content types
        """

        response = page.setup_request(request)
        if response:
            return response

        for content in page.content.all_of_type(tuple(page._feincms_content_types_with_process)):
            r = content.process(request)
            if r:
                return r

    def render(self, request, page):
        # This facility can be used by request processors to add values
        # to the context.
        extra_context = getattr(request, '_feincms_extra_context', {})
        return render_to_response(page.template.path, {
            'feincms_page' : page,
            }, context_instance=RequestContext(request, extra_context))

    def finalize(self, request, response, page):
        for content in page.content.all_of_type(tuple(page._feincms_content_types_with_finalize)):
            r = content.finalize(request, response)
            if r:
                return r

        page.finalize_response(request, response)

        # Add never cache headers in case frontend editing is active
        if hasattr(request, "session") and request.session.get('frontend_editing', False):
            add_never_cache_headers(response)

        return response

# Backards compatibility. Instantiate default handler
handler = Handler()


class PreviewHandler(Handler):
    """
    This handler is for previewing site content; it takes a page_id so
    the page is uniquely identified and does not care whether the page
    is active or expired. To balance that, it requires a logged in user.
    """

    def __call__(self, request, page_id):
        page = get_object_or_404(Page, pk=page_id)
        return self.build_response(request, page)

    def finalize(self, request, response, page):
        """
        Do (nearly) nothing
        """

        add_never_cache_headers(response)
        return response


preview_handler = permission_required('page.change_page')(PreviewHandler())

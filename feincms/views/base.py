from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from feincms.module.page.models import Page


def _build_page_response(page, request):
    response = page.setup_request(request)
    
    if response is None:
        extra_context = request._feincms_extra_context
        response = render_to_response(page.template.path, {
            'feincms_page': page,
            }, context_instance=RequestContext(request, extra_context))

    return response

def build_page_response(page, request):
    response = _build_page_response(page, request)
    page.finalize_response(request, response)
    return response

def handler(request, path=None):
    """
    This is the default handler for feincms page content.
    """
    if path is None:
        path = request.path

    page = Page.objects.page_for_path_or_404(path)

    response = build_page_response(page, request)

    return response


@permission_required('page.change_page')
def preview_handler(request, page_id):
    """
    This handler is for previewing site content; it takes a page_id so
    the page is uniquely identified and does not care whether the page
    is active or expired. To balance that, it requires a logged in user.
    """
    page = get_object_or_404(Page, pk=page_id)
    return _build_page_response(page, request)

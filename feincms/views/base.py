from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.cache import add_never_cache_headers
from django.contrib.sites.models import RequestSite

from feincms.module.page.models import Page


def _build_page_response(page, request):
    extra_context = request._feincms_extra_context
    return render_to_response(page.template.path, {
        'feincms_page' : page,
        'feincms_site' : RequestSite(request),
        }, context_instance=RequestContext(request, extra_context))

def build_page_response(page, request):
    response = page.setup_request(request)
    if response:
        return response

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

    if hasattr(request, "session") and request.session.get('frontend_editing', False):
        add_never_cache_headers(response)

    return response


@permission_required('page.change_page')
def preview_handler(request, page_id):
    """
    This handler is for previewing site content; it takes a page_id so
    the page is uniquely identified and does not care whether the page
    is active or expired. To balance that, it requires a logged in user.
    """
    page = get_object_or_404(Page, pk=page_id)
    # Note: Does not call finalize_response so that response processors
    # will not kick in, as they might cache the page or do something
    # equally inappropriate. We are just previewing the page, move along.
    page.setup_request(request)
    return _build_page_response(page, request)


from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from feincms.module.page.models import Page

def build_page_response(page, request):
    response = page.setup_request(request) or \
               render_to_response(page.template.path, {
                    'feincms_page': page,
                    }, context_instance=RequestContext(request))

    return response

def handler(request, path=None):
    """
    This is the default handler for feincms page content.
    """
    if path is None:
        path = request.path

    page = Page.objects.page_for_path_or_404(path)
    return build_page_response(page, request)

# XXX Needs more restrictive permissions than just "logged in"!!
@login_required
def preview_handler(request, page_id):
    """
    This handler is for previewing site content; it takes a page_id so
    the page is uniquely identified and does not care whether the page
    is active or expired. To balance that, it requires a logged in user.
    """
    page = get_object_or_404(Page, pk=page_id)
    return build_page_response(page, request)

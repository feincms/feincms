from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from feincms.module.page.models import Page
from feincms.views.decorators import infanta_exclude


def build_page_response(page, request):
    response = page.setup_request(request) or \
               render_to_response(page.template.path, {
                    'feincms_page': page,
                    }, context_instance=RequestContext(request))

    return response


@infanta_exclude
def handler(request, path=None):
    """
    This is the default handler for feincms page content.
    """
    if path is None:
        path = request.path

    page = Page.objects.page_for_path_or_404(path)

    return build_page_response(page, request)


@infanta_exclude
@permission_required('page.change_page')
def preview_handler(request, page_id):
    """
    This handler is for previewing site content; it takes a page_id so
    the page is uniquely identified and does not care whether the page
    is active or expired. To balance that, it requires a logged in user.
    """
    page = get_object_or_404(Page, pk=page_id)
    return build_page_response(page, request)

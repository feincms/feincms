from django.http import Http404

from feincms.content.application.models import retrieve_page_information
from feincms.module.page.models import Page
from feincms.views.base import _build_page_response


def handler(request, path=None):
    if path is None:
        path = request.path

    page = Page.objects.best_match_for_path(path, raise404=True)

    applicationcontents = page.applicationcontent_set.all()

    if request.path != page.get_absolute_url():
        # The best_match logic kicked in. See if we have at least one
        # application content for this page, and raise a 404 otherwise.

        if not applicationcontents:
            raise Http404

    # The monkey-patched reverse() method needs some information
    # for proximity analysis when determining the nearest
    # application integration point
    retrieve_page_information(page)

    response = page.setup_request(request)
    if response:
        return response

    for content in applicationcontents:
        r = content.process(request)
        if r and (r.status_code != 200 or request.is_ajax()):
            return r

    response = _build_page_response(page, request)
    page.finalize_response(request, response)
    return response

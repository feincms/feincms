from django.http import Http404

from feincms.module.page.models import Page
from feincms.views.base import build_page_response
from feincms.views.decorators import infanta_exclude


@infanta_exclude
def handler(request, path=None):
    if path is None:
        path = request.path

    page = Page.objects.best_match_for_path(path, raise404=True)

    if request.path != page.get_absolute_url():
        # The best_match logic kicked in. See if we have at least one
        # application content for this page, and raise a 404 otherwise.

        if not page.applicationcontent_set.count():
            raise Http404

    return build_page_response(page, request)


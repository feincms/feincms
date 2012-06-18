from django.http import Http404
from django.shortcuts import get_object_or_404

from feincms.module.page.models import Page
from feincms.views.cbv.views import Handler


class PreviewHandler(Handler):
    """
    Preview handler

    The methods used in this handler should not be considered official API.

    *** Everything here is subject to change. ***
    """

    def handler(self, request, path, page_id):
        if not request.user.is_staff:
            raise Http404()

        page = get_object_or_404(Page, pk=page_id)

        # Remove _preview/42/ from URL, the rest of the handler code should not
        # know that anything about previewing. Handler.prepare will still raise
        # a 404 if the extra_path isn't consumed by any content type
        request.path = page.get_absolute_url()

        response = self.handle_object(page)
        response['Cache-Control'] = 'no-cache, must-revalidate, no-store, private'
        return response

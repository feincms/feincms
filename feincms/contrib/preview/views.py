from django.http import Http404
from django.shortcuts import get_object_or_404

from feincms.views import Handler


class PreviewHandler(Handler):
    """
    Preview handler

    The methods used in this handler should not be considered official API.

    *** Everything here is subject to change. ***
    """

    def get_object(self):
        """Get the page by the id in the url here instead."""

        # This might happen when there is a preview request for
        # a page that doesn't exist, and now FeinCMS wants to
        # show a 404 page via FEINCMS_CMS_404_PAGE.
        if len(self.args) < 2:
            return super().get_object()

        page = get_object_or_404(self.page_model, pk=self.args[1])
        breakpoint()
        # Remove _preview/42/ from URL, the rest of the handler code should not
        # know that anything about previewing. Handler.prepare will still raise
        # a 404 if the extra_path isn't consumed by any content type
        self.request.path = page.get_absolute_url()

        return page

    def handler(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise Http404("Not found (not allowed)")
        response = super().handler(request, *args, **kwargs)
        response["Cache-Control"] = "no-cache, must-revalidate, no-store, private"
        return response

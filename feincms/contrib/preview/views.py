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
            raise Http404

        self.page = get_object_or_404(Page, pk=page_id)

        # Throw out request processor which will cause the page to-be-previewed
        # to be seen as inactive (which is the case, of course)
        self.page.request_processors = self.page.request_processors.copy()
        self.page.register_request_processor(
            lambda page, response: None, # Do nothing
            key='path_active')

        # Remove _preview/42/ from URL, the rest of the handler code should not
        # know that anything about previewing. Handler.prepare will still raise
        # a 404 if the extra_path isn't consumed by any content type
        request.path = self.page.get_absolute_url()

        response = self.prepare()
        if response:
            return response

        response = self.render_to_response(self.get_context_data())
        response = self.finalize(response)
        response['Cache-Control'] = 'no-cache, must-revalidate, no-store, private'
        return response

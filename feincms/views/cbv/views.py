from django.http import Http404

from feincms import settings
from feincms.module.mixins import ContentView
from feincms.module.page.models import Page


class HandlerBase(ContentView):
    """
    Class-based handler for FeinCMS page content
    """

    context_object_name = 'feincms_page'

    def get(self, request, *args, **kwargs):
        return self.handler(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.handler(request, *args, **kwargs)

    def handler(self, request, *args, **kwargs):
        page = Page.objects.for_request(request,
            raise404=True, best_match=True, setup=False)

        return self.handle_object(page)


# ------------------------------------------------------------------------
class Handler(HandlerBase):
    def handler(self, request, *args, **kwargs):
        try:
            return super(Handler, self).handler(request, *args, **kwargs)
        except Http404, e:
            if settings.FEINCMS_CMS_404_PAGE:
                try:
                    request.original_path_info = request.path_info
                    request.path_info = settings.FEINCMS_CMS_404_PAGE
                    response = super(Handler, self).handler(request, *args, **kwargs)
                    response.status_code = 404
                    return response
                except Http404:
                    raise e
            else:
                raise

# ------------------------------------------------------------------------

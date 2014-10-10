from __future__ import absolute_import, unicode_literals

from django.http import Http404
from django.utils.functional import cached_property

from feincms import settings
from feincms._internal import get_model
from feincms.module.mixins import ContentView


class Handler(ContentView):
    page_model_path = None
    context_object_name = 'feincms_page'

    @cached_property
    def page_model(self):
        model = self.page_model_path or settings.FEINCMS_DEFAULT_PAGE_MODEL
        return get_model(*model.split('.'))

    def get_object(self):
        path = None
        if self.args:
            path = self.args[0]
        return self.page_model._default_manager.for_request(
            self.request, raise404=True, best_match=True, path=path)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(Handler, self).dispatch(request, *args, **kwargs)
        except Http404 as e:
            if settings.FEINCMS_CMS_404_PAGE:
                try:
                    request.original_path_info = request.path_info
                    request.path_info = settings.FEINCMS_CMS_404_PAGE
                    response = super(Handler, self).dispatch(
                        request, *args, **kwargs)
                    response.status_code = 404
                    return response
                except Http404:
                    raise e
            else:
                raise

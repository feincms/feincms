from __future__ import absolute_import, unicode_literals

from django.db.models import get_model
from django.http import Http404

from feincms import settings
from feincms.module.mixins import ContentView


class Handler(ContentView):
    page_model_path = 'page.Page'
    context_object_name = 'feincms_page'

    @property
    def page_model(self):
        if not hasattr(self, '_page_model'):
            self._page_model = get_model(*self.page_model_path.split('.'))
            if self._page_model is None:
                raise ImportError(
                    "Can't import model \"%s\"" % self.page_model_path)
        return self._page_model

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

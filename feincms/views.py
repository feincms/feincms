from __future__ import absolute_import, unicode_literals

import logging

from django.apps import apps
from django.http import Http404
from django.utils.functional import cached_property

from feincms import settings
from feincms.module.mixins import ContentView


logger = logging.getLogger(__name__)


class Handler(ContentView):
    page_model_path = None
    context_object_name = 'feincms_page'

    @cached_property
    def page_model(self):
        model = self.page_model_path or settings.FEINCMS_DEFAULT_PAGE_MODEL
        return apps.get_model(*model.split('.'))

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
            if settings.FEINCMS_CMS_404_PAGE is not None:
                logger.info(
                    "Http404 raised for '%s', attempting redirect to"
                    " FEINCMS_CMS_404_PAGE", args[0])
                try:
                    # Fudge environment so that we end up resolving the right
                    # page.
                    # Note: request.path is used by the page redirect processor
                    # to determine if the redirect can be taken, must be == to
                    # page url.
                    # Also clear out the _feincms_page attribute which caches
                    # page lookups (and would just re-raise a 404).
                    request.path = request.path_info =\
                        settings.FEINCMS_CMS_404_PAGE
                    if hasattr(request, '_feincms_page'):
                        delattr(request, '_feincms_page')
                    response = super(Handler, self).dispatch(
                        request, settings.FEINCMS_CMS_404_PAGE, **kwargs)
                    # Only set status if we actually have a page. If we get for
                    # example a redirect, overwriting would yield a blank page
                    if response.status_code == 200:
                        response.status_code = 404
                    return response
                except Http404:
                    logger.error(
                        "Http404 raised while resolving"
                        " FEINCMS_CMS_404_PAGE=%s",
                        settings.FEINCMS_CMS_404_PAGE)
                    raise e
            else:
                raise

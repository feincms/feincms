# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from collections import defaultdict

from django.http import Http404

from feincms import settings
from feincms.content.application.models import ApplicationContent
from feincms.module.page.models import Page
from feincms.views.base import Handler


def applicationcontent_request_processor(page, request):
    if not hasattr(request, '_feincms_appcontent_parameters'):
        request._feincms_appcontent_parameters = dict(in_appcontent_subpage=False)

    if request.path != page.get_absolute_url():
        # The best_match logic kicked in. See if we have at least one
        # application content for this page, and raise a 404 otherwise.
        if not page.content.all_of_type(ApplicationContent):
            if not settings.FEINCMS_ALLOW_EXTRA_PATH:
                raise Http404
        else:
            request._feincms_appcontent_parameters['in_appcontent_subpage'] = True

        extra_path = request.path[len(page.get_absolute_url()):]
        extra = extra_path.strip('/').split('/')
        request._feincms_appcontent_parameters['page_extra_path'] = extra
        request.extra_path = extra_path
    else:
        request.extra_path = ""

Page.register_request_processors(applicationcontent_request_processor)


class ApplicationContentHandler(Handler):
    def __call__(self, request, path=None):
        request._feincms_appcontent_parameters = {}

        return self.build_response(request,
            Page.objects.best_match_for_path(path or request.path, raise404=True))

handler = ApplicationContentHandler()

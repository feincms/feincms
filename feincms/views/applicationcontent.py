# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from collections import defaultdict

from django.http import Http404

from feincms import settings
from feincms.module.page.models import Page
from feincms.views.base import Handler

try:
    any
except NameError:
    # For Python 2.4
    from feincms.compat import c_any as any



class ApplicationContentHandler(Handler):
    def __call__(self, request, path=None):
        return self.build_response(request,
            Page.objects.best_match_for_path(path or request.path))

    def prepare(self, request, page):
        # prepare storage for rendered application contents
        if not hasattr(request, '_feincms_applicationcontents'):
            request._feincms_applicationcontents = {}
            request._feincms_applicationcontents_headers = defaultdict(list)

        # Used to provide additional app-specific context variables:
        if not hasattr(request, '_feincms_appcontent_parameters'):
            request._feincms_appcontent_parameters = dict(in_appcontent_subpage=False)

        has_appcontent = page_has_appcontent(page)

        if request.path != page.get_absolute_url():
            # The best_match logic kicked in. See if we have at least one
            # application content for this page, and raise a 404 otherwise.
            if not has_appcontent:
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

        response = page.setup_request(request)
        if response:
            return response

        if has_appcontent:
            for content in page.applicationcontent_set.all():
                r = content.process(request)
                if r and (r.status_code != 200 or request.is_ajax() or getattr(r, 'standalone', False)):
                    return r

    def finalize(self, request, response, page):
        # This should go into finalize()
        _update_response_headers(request, page_has_appcontent(page), response)
        return super(ApplicationContentHandler, self).finalize(request, response, page)

handler = ApplicationContentHandler()


def page_has_appcontent(page):
    from feincms.content.application.models import ApplicationContent
    return any(page.content.all_of_type(ApplicationContent))


# ------------------------------------------------------------------------
def _update_response_headers(request, has_appcontent, response):
    """
    Combine all headers that were set by the different content types
    We are interested in Cache-Control, Last-Modified, Expires
    """
    from django.utils.http import http_date

    # Ideally, for the Cache-Control header, we'd want to do some intelligent
    # combining, but that's hard. Let's just collect and unique them and let
    # the client worry about that.
    cc_headers = set()
    for x in (cc.split(",") for cc in request._feincms_applicationcontents_headers['Cache-Control']):
        cc_headers |= set((s.strip() for s in x))

    if len(cc_headers):
        response['Cache-Control'] = ", ".join(cc_headers)
    else:   # Default value
        if has_appcontent:
            response['Cache-Control'] = 'no-cache, must-revalidate'

    # Check all Last-Modified headers, choose the latest one
    from email.utils import parsedate
    from time import mktime

    lm_list = [parsedate(x) for x in request._feincms_applicationcontents_headers['Last-Modified']]
    if len(lm_list) > 0:
        response['Last-Modified'] = http_date(mktime(max(lm_list)))

    # Check all Expires headers, choose the earliest one
    lm_list = [parsedate(x) for x in request._feincms_applicationcontents_headers['Expires']]
    if len(lm_list) > 0:
        response['Expires'] = http_date(mktime(min(lm_list)))


# ------------------------------------------------------------------------

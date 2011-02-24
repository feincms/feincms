# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

try:
    from email.utils import parsedate
except ImportError: # py 2.4 compat
    from email.Utils import parsedate

from django.http import Http404
from django.utils.cache import add_never_cache_headers

from feincms import settings
from feincms.content.application.models import retrieve_page_information
from feincms.module.page.models import Page
from feincms.views.base import _build_page_response

try:
    any
except NameError:
    # For Python 2.4
    from feincms.compat import c_any as any

# ------------------------------------------------------------------------
# TODO: This routine is very similar to the one in base.py, perhaps we should look into unifying them?

def handler(request, path=None):
    if path is None:
        path = request.path

    # prepare storage for rendered application contents
    if not hasattr(request, '_feincms_applicationcontents'):
        request._feincms_applicationcontents = {}
        request._feincms_applicationcontents_headers = {}

    # Used to provide additional app-specific context variables:
    if not hasattr(request, '_feincms_appcontent_parameters'):
        request._feincms_appcontent_parameters = dict(in_appcontent_subpage = False)

    page = Page.objects.best_match_for_path(path, raise404=True)
    response = build_page_response(page, request)

    if hasattr(request, "session") and request.session.get('frontend_editing', False):
        add_never_cache_headers(response)

    return response

def _page_has_appcontent(page):
    # Very dumb implementation, will be overridden with a more efficient
    # version if ct_tracker is enabled.
    try:
        applicationcontents = page.applicationcontent_set.all()
    except AttributeError:
        return False

    has_appcontent = any(applicationcontents)

    return has_appcontent

page_has_appcontent = _page_has_appcontent

def build_page_response(page, request):
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

    # The monkey-patched reverse() method needs some information
    # for proximity analysis when determining the nearest
    # application integration point
    retrieve_page_information(page)

    response = page.setup_request(request)
    if response:
        return response

    if has_appcontent:
        for content in page.applicationcontent_set.all():
            r = content.process(request)
            if r and (r.status_code != 200 or request.is_ajax() or getattr(r, 'standalone', False)):
                return r

    response = _build_page_response(page, request)

    _update_response_headers(request, has_appcontent, response)

    page.finalize_response(request, response)

    return response

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
    for x in (cc.split(",") for cc in request._feincms_applicationcontents_headers.get('Cache-Control', ())):
        cc_headers |= set((s.strip() for s in x))

    if len(cc_headers):
        response['Cache-Control'] = ", ".join(cc_headers)
    else:   # Default value
        if has_appcontent:
            response['Cache-Control'] = 'no-cache, must-revalidate'

    # Check all Last-Modified headers, choose the latest one
    from time import mktime

    lm_list = [parsedate(x) for x in request._feincms_applicationcontents_headers.get('Last-Modified', ())]
    if len(lm_list) > 0:
        response['Last-Modified'] = http_date(mktime(max(lm_list)))

    # Check all Expires headers, choose the earliest one
    lm_list = [parsedate(x) for x in request._feincms_applicationcontents_headers.get('Expires', ())]
    if len(lm_list) > 0:
        response['Expires'] = http_date(mktime(min(lm_list)))


# ------------------------------------------------------------------------

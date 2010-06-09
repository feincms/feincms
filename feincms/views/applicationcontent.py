# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

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
    page.finalize_response(request, response)

    return response

# ------------------------------------------------------------------------

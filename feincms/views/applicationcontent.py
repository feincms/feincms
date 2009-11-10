# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django.http import Http404

from feincms import settings
from feincms.content.application.models import retrieve_page_information
from feincms.module.page.models import Page
from feincms.views.base import _build_page_response

# ------------------------------------------------------------------------
# TODO: This routine is very similar to the one in base.py, perhaps we should look into unifying them?

def handler(request, path=None):
    if path is None:
        path = request.path

    # prepare storage for rendered application contents
    if not hasattr(request, '_feincms_applicationcontents'):
        request._feincms_applicationcontents = {}
        request._feincms_applicationcontents_fragments = {}

    # Used to provide additional app-specific context variables:
    if not hasattr(request, '_feincms_appcontent_parameters'):
        request._feincms_appcontent_parameters = {"in_appcontent_subpage": False}

    page = Page.objects.best_match_for_path(path, raise404=True)
    return build_page_response(page, request)


def build_page_response(page, request):
    from django.core.cache import cache as django_cache

    # Try to avoid the lookup of app contents by caching, since nodes
    # with app content are a rather rare occurrence, this is a win in
    # most cases.
    has_appcontent = True
    if settings.FEINCMS_USE_CACHE:
        ck = 'HAS-APP-CONTENT-' + page.cache_key()
        has_appcontent = django_cache.get(ck, True)

    if has_appcontent:
        applicationcontents = page.applicationcontent_set.all()
        has_appcontent = any(applicationcontents)
        if settings.FEINCMS_USE_CACHE:
            django_cache.set(ck, has_appcontent)

    if request.path != page.get_absolute_url():
        # The best_match logic kicked in. See if we have at least one
        # application content for this page, and raise a 404 otherwise.
        if not has_appcontent:
            raise Http404
        else:
            request._feincms_appcontent_parameters['in_appcontent_subpage'] = True

    # The monkey-patched reverse() method needs some information
    # for proximity analysis when determining the nearest
    # application integration point
    retrieve_page_information(page)

    response = page.setup_request(request)
    if response:
        return response

    if has_appcontent:
        for content in applicationcontents:
            r = content.process(request)
            if r and (r.status_code != 200 or request.is_ajax() or getattr(r, 'standalone', False)):
                return r

    response = _build_page_response(page, request)
    page.finalize_response(request, response)
    return response

# ------------------------------------------------------------------------

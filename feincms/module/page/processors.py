from __future__ import absolute_import, print_function, unicode_literals

import re
import sys

from django.conf import settings as django_settings
from django.http import Http404, HttpResponseRedirect
from django.utils.cache import add_never_cache_headers


def redirect_request_processor(page, request):
    """
    Returns a ``HttpResponseRedirect`` instance if the current page says
    a redirect should happen.
    """
    target = page.get_redirect_to_target(request)
    if target:
        if request._feincms_extra_context.get('extra_path', '/') == '/':
            return HttpResponseRedirect(target)
        raise Http404()


def extra_context_request_processor(page, request):
    """
    Fills ``request._feincms_extra_context`` with a few useful variables.
    """
    request._feincms_extra_context.update({
        # XXX This variable name isn't accurate anymore.
        'in_appcontent_subpage': False,
        'extra_path': '/',
    })

    url = page.get_absolute_url()
    if request.path != url:
        request._feincms_extra_context.update({
            'in_appcontent_subpage': True,
            'extra_path': re.sub(
                '^' + re.escape(url.rstrip('/')),
                '',
                request.path,
            ),
        })


def frontendediting_request_processor(page, request):
    """
    Sets the frontend editing state in the cookie depending on the
    ``frontend_editing`` GET parameter and the user's permissions.
    """
    if 'frontend_editing' not in request.GET:
        return

    response = HttpResponseRedirect(request.path)
    if request.user.has_module_perms('page'):
        try:
            enable_fe = int(request.GET['frontend_editing']) > 0
        except ValueError:
            enable_fe = False

        if enable_fe:
            response.set_cookie(str('frontend_editing'), enable_fe)
        else:
            response.delete_cookie(str('frontend_editing'))

    # Redirect to cleanup URLs
    return response


def frontendediting_response_processor(page, request, response):
    # Add never cache headers in case frontend editing is active
    if (hasattr(request, 'COOKIES')
            and request.COOKIES.get('frontend_editing', False)):

        if hasattr(response, 'add_post_render_callback'):
            response.add_post_render_callback(add_never_cache_headers)
        else:
            add_never_cache_headers(response)


def etag_request_processor(page, request):
    """
    Short-circuits the request-response cycle if the ETag matches.
    """

    # XXX is this a performance concern? Does it create a new class
    # every time the processor is called or is this optimized to a static
    # class??
    class DummyResponse(dict):
        """
        This is a dummy class with enough behaviour of HttpResponse so we
        can use the condition decorator without too much pain.
        """
        def has_header(page, what):
            return False

    def dummy_response_handler(*args, **kwargs):
        return DummyResponse()

    def etagger(request, page, *args, **kwargs):
        etag = page.etag(request)
        return etag

    def lastmodifier(request, page, *args, **kwargs):
        lm = page.last_modified()
        return lm

    # Unavailable in Django 1.0 -- the current implementation of ETag support
    # requires Django 1.1 unfortunately.
    from django.views.decorators.http import condition

    # Now wrap the condition decorator around our dummy handler:
    # the net effect is that we will be getting a DummyResponse from
    # the handler if processing is to continue and a non-DummyResponse
    # (should be a "304 not modified") if the etag matches.
    rsp = condition(etag_func=etagger, last_modified_func=lastmodifier)(
        dummy_response_handler)(request, page)

    # If dummy then don't do anything, if a real response, return and
    # thus shortcut the request processing.
    if not isinstance(rsp, DummyResponse):
        return rsp


def etag_response_processor(page, request, response):
    """
    Response processor to set an etag header on outgoing responses.
    The Page.etag() method must return something valid as etag content
    whenever you want an etag header generated.
    """
    etag = page.etag(request)
    if etag is not None:
        response['ETag'] = '"' + etag + '"'


def debug_sql_queries_response_processor(verbose=False, file=sys.stderr):
    """
    Attaches a handler which prints the query count (and optionally all
    individual queries which have been executed) on the console. Does nothing
    if ``DEBUG = False``.

    Example::

        from feincms.module.page import models, processors
        models.Page.register_response_processor(
            processors.debug_sql_queries_response_processor(verbose=True),
            )
    """
    if not django_settings.DEBUG:
        return lambda page, request, response: None

    def processor(page, request, response):
        from django.db import connection

        print_sql = lambda x: x
        try:
            import sqlparse
            print_sql = lambda x: sqlparse.format(
                x, reindent=True, keyword_case='upper')
        except:
            pass

        if verbose:
            print("-" * 60, file=file)
        time = 0.0
        i = 0
        for q in connection.queries:
            i += 1
            if verbose:
                print("%d : [%s]\n%s\n" % (
                    i, q['time'], print_sql(q['sql'])), file=file)
            time += float(q['time'])

        print("-" * 60, file=file)
        print("Total: %d queries, %.3f ms" % (i, time), file=file)
        print("-" * 60, file=file)

    return processor

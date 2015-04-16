from __future__ import absolute_import, print_function, unicode_literals

import logging
import re
import sys

from django.conf import settings as django_settings
from django.http import Http404, HttpResponseRedirect


logger = logging.getLogger(__name__)


def redirect_request_processor(page, request):
    """
    Returns a ``HttpResponseRedirect`` instance if the current page says
    a redirect should happen.
    """
    target = page.get_redirect_to_target(request)
    if target:
        extra_path = request._feincms_extra_context.get('extra_path', '/')
        if extra_path == '/':
            return HttpResponseRedirect(target)
        logger.debug(
            "Page redirect on '%s' not taken because extra path '%s' present",
            page.get_absolute_url(), extra_path)
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

        try:
            import sqlparse

            def print_sql(x):
                return sqlparse.format(
                    x, reindent=True, keyword_case='upper')
        except:
            def print_sql(x):
                return x

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

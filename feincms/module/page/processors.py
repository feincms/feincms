import sys

from django.conf import settings as django_settings
from django.http import Http404, HttpResponseRedirect


def require_path_active_request_processor(page, request):
    """
    Checks whether any ancestors are actually inaccessible (ie. not
    inactive or expired) and raise a 404 if so.
    """
    if not page.are_ancestors_active():
        raise Http404()


def redirect_request_processor(page, request):
    target = page.get_redirect_to_target(request)
    if target:
        if request._feincms_extra_context.get('extra_path', '/') == '/':
            return HttpResponseRedirect(target)
        raise Http404()

def frontendediting_request_processor(page, request):
    if not 'frontend_editing' in request.GET:
        return

    if request.user.has_module_perms('page'):
        try:
            enable_fe = int(request.GET['frontend_editing']) > 0
        except ValueError:
            enable_fe = False

        request.session['frontend_editing'] = enable_fe

    # Redirect to cleanup URLs
    return HttpResponseRedirect(request.path)


def etag_request_processor(page, request):

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
    rsp = condition(etag_func=etagger, last_modified_func=lastmodifier)(dummy_response_handler)(request, page)

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
    if not django_settings.DEBUG:
        return lambda page, request, response: None

    def processor(page, request, response):
        from django.db import connection

        print_sql = lambda x: x
        try:
            import sqlparse
            print_sql = lambda x: sqlparse.format(x, reindent=True, keyword_case='upper')
        except:
            pass

        if verbose:
            print >> file, "--------------------------------------------------------------"
        time = 0.0
        i = 0
        for q in connection.queries:
            i += 1
            if verbose:
                print >> file, "%d : [%s]\n%s\n" % ( i, q['time'], print_sql(q['sql']))
            time += float(q['time'])

        print >> file, "--------------------------------------------------------------"
        print >> file, "Total: %d queries, %.3f ms" % (i, time)
        print >> file, "--------------------------------------------------------------"

    return processor

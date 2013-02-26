from django.http import HttpResponse
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from feincms.module.page.models import Page


def standalone(view_func):
    """
    Marks the view method as standalone view; this means that
    ``HttpResponse`` objects returned from ``ApplicationContent``
    are returned directly, without further processing.
    """

    def inner(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            response.standalone = True
        return response
    return wraps(view_func)(inner)

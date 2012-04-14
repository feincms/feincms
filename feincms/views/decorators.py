from django.http import HttpResponse
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from feincms.module.page.models import Page


def add_page_to_extra_context(view_func):
    """
    Adds the best-match page to the extra_context keyword argument. Mainly used
    to provide generic views which integrate into the page module.
    """

    def inner(request, *args, **kwargs):
        import warnings
        warnings.warn("The `add_page_to_extra_context` view decorator has been"
            " deprecated, as have the function-based generic views in"
            " `django.views.generic` and `feincms.views.generic`. Use the"
            " `feincms.context_processors.add_page_if_missing` context processor"
            " and Django's class-based generic views instead.",
            DeprecationWarning, stacklevel=2)

        kwargs.setdefault('extra_context', {})
        kwargs['extra_context']['feincms_page'] = Page.objects.for_request(
            request, best_match=True)

        return view_func(request, *args, **kwargs)
    return wraps(view_func)(inner)


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

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
        kwargs.setdefault('extra_context', {})
        kwargs['extra_context']['feincms_page'] = Page.objects.best_match_for_request(request)

        return view_func(request, *args, **kwargs)
    return wraps(view_func)(inner)


def infanta_exclude(view_func):
    """
    Marks the function so that it is excluded from infanta handling

    This does not change anything if you do not use the InfantaMiddleware (the
    common case)
    """

    view_func._infanta_exclude = True
    return view_func


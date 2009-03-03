try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from feincms.module.page.models import Page


def add_page_to_extra_context(view_func):
    def inner(request, *args, **kwargs):
        kwargs.setdefault('extra_context', {})
        kwargs['extra_context']['feincms_page'] = Page.objects.best_match_for_request(request)

        return view_func(request, *args, **kwargs)
    return wraps(view_func)(inner)


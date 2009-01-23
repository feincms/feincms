try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from feincms.models import Page


def add_page_to_extra_context(view_func):
    def inner(request, *args, **kwargs):
        kwargs.setdefault('extra_context', {})
        kwargs['extra_context']['page'] = Page.objects.best_match_for_path(request.path)

        return view_func(request, *args, **kwargs)
    return wraps(view_func)(inner)


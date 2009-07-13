try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps


def infanta_exclude(view_func):
    """
    Marks the function so that it is excluded from infanta handling

    This does not change anything if you do not use the InfantaMiddleware (the
    common case)
    """

    view_func._infanta_exclude = True
    return view_func

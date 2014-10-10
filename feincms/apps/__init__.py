from __future__ import absolute_import

from functools import wraps

from django.http import HttpResponse
from django.template.response import TemplateResponse

from .contents import ApplicationContent
from .reverse import app_reverse, app_reverse_lazy, permalink


__all__ = (
    'ApplicationContent',
    'app_reverse', 'app_reverse_lazy', 'permalink',
    'UnpackTemplateResponse', 'standalone', 'unpack',
)


class UnpackTemplateResponse(TemplateResponse):
    """
    Completely the same as marking applicationcontent-contained views with
    the ``feincms.views.decorators.unpack`` decorator.
    """
    _feincms_unpack = True


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


def unpack(view_func):
    """
    Marks the returned response as to-be-unpacked if it is a
    ``TemplateResponse``.
    """

    def inner(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        if isinstance(response, TemplateResponse):
            response._feincms_unpack = True
        return response
    return wraps(view_func)(inner)

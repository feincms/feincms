from __future__ import absolute_import, unicode_literals

from functools import wraps

from django.http import HttpResponse
from django.template.response import TemplateResponse


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

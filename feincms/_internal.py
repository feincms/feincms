"""
These are internal helpers. Do not rely on their presence.

http://mail.python.org/pipermail/python-dev/2008-January/076194.html
"""

from __future__ import absolute_import, unicode_literals

from distutils.version import LooseVersion
from django import get_version
from django.template.loader import render_to_string


__all__ = (
    'monkeypatch_method', 'monkeypatch_property',
)


def monkeypatch_method(cls):
    """
    A decorator to add a single method to an existing class::

        @monkeypatch_method(<someclass>)
        def <newmethod>(self, [...]):
            pass
    """

    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


def monkeypatch_property(cls):
    """
    A decorator to add a single method as a property to an existing class::

        @monkeypatch_property(<someclass>)
        def <newmethod>(self, [...]):
            pass
    """

    def decorator(func):
        setattr(cls, func.__name__, property(func))
        return func
    return decorator


if LooseVersion(get_version()) < LooseVersion('1.10'):
    def ct_render_to_string(template, ctx, **kwargs):
        from django.template import RequestContext

        context_instance = kwargs.get('context')
        if context_instance is None and kwargs.get('request'):
            context_instance = RequestContext(kwargs['request'])

        return render_to_string(
            template,
            ctx,
            context_instance=context_instance)
else:
    def ct_render_to_string(template, ctx, **kwargs):
        return render_to_string(
            template,
            ctx,
            request=kwargs.get('request'))

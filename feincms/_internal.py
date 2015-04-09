"""
These are internal helpers. Do not rely on their presence.

http://mail.python.org/pipermail/python-dev/2008-January/076194.html
"""

from __future__ import absolute_import, unicode_literals


__all__ = (
    'get_model', 'get_models', 'monkeypatch_method', 'monkeypatch_property',
)


try:
    from django.apps import apps
    get_model = apps.get_model
    get_models = apps.get_models

except ImportError:
    from django.db.models import get_model, get_models


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

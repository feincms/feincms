"""
These are internal helpers. Do not rely on their presence.

http://mail.python.org/pipermail/python-dev/2008-January/076194.html
"""

from __future__ import absolute_import, unicode_literals


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


def monkeypatch_class(name, bases, namespace):
    """
    A metaclass to add a number of methods (or other attributes) to an
    existing class, using a convenient class notation::

        class <newclass>(<someclass>):
            __metaclass__ = monkeypatch_class
            def <method1>(...): ...
            def <method2>(...): ...
            ...
    """

    assert len(bases) == 1, "Exactly one base class required"
    base = bases[0]
    for name, value in namespace.iteritems():
        if name != "__metaclass__":
            setattr(base, name, value)
    return base


def get_model_name(opts):
    try:
        return opts.model_name
    except AttributeError:
        return opts.module_name


def get_permission_codename(action, opts):
    """
    Backport of django.contrib.auth.get_permission_codename for older versions
    of Django.
    """
    return '%s_%s' % (action, get_model_name(opts))

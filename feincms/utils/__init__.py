# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, division, unicode_literals

import re

from importlib import import_module

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.models import AutoField
from django.utils import six

from feincms import settings


# ------------------------------------------------------------------------
def get_object(path, fail_silently=False):
    # Return early if path isn't a string (might already be an callable or
    # a class or whatever)
    if not isinstance(path, six.string_types):  # XXX bytes?
        return path

    try:
        return import_module(path)
    except ImportError:
        try:
            dot = path.rindex('.')
            mod, fn = path[:dot], path[dot + 1:]

            return getattr(import_module(mod), fn)
        except (AttributeError, ImportError):
            if not fail_silently:
                raise


# ------------------------------------------------------------------------
def get_model_instance(app_label, model_name, pk):
    """
    Find an object instance given an app_label, a model name and the
    object's pk.

    This is used for page's get_link_target but can be used for other
    content types that accept e.g. either an internal or external link.
    """

    model = apps.get_model(app_label, model_name)
    if not model:
        return None

    try:
        instance = model._default_manager.get(pk=pk)
        return instance
    except model.DoesNotExist:
        pass

    return None


# ------------------------------------------------------------------------
REDIRECT_TO_RE = re.compile(
    r'^(?P<app_label>\w+).(?P<model_name>\w+):(?P<pk>\d+)$')


def match_model_string(s):
    """
    Try to parse a string in format "app_label.model_name:pk", as is used
    Page.get_link_target()

    Returns a tuple app_label, model_name, pk or None if the string
    does not match the expected format.
    """

    match = REDIRECT_TO_RE.match(s)
    if not match:
        return None
    matches = match.groupdict()
    return (matches['app_label'], matches['model_name'], int(matches['pk']))


# ------------------------------------------------------------------------
def copy_model_instance(obj, exclude=None):
    """
    Copy a model instance, excluding primary key and optionally a list
    of specified fields.
    """

    exclude = exclude or ()
    initial = dict(
        (f.name, getattr(obj, f.name)) for f in obj._meta.fields
        if not isinstance(f, AutoField) and f.name not in exclude and
        f not in obj._meta.parents.values())
    return obj.__class__(**initial)


# ------------------------------------------------------------------------
def shorten_string(str, max_length=50, ellipsis=' … '):
    """
    Shorten a string for display, truncate it intelligently when too long.
    Try to cut it in 2/3 + ellipsis + 1/3 of the original title. Also try to
    cut the first part off at a white space boundary instead of in mid-word.
    """

    if len(str) >= max_length:
        first_part = int(max_length * 0.6)
        next_space = str[first_part:(max_length // 2 - first_part)].find(' ')
        if (next_space >= 0 and
                first_part + next_space + len(ellipsis) < max_length):
            first_part += next_space
        return (
            str[:first_part] +
            ellipsis +
            str[-(max_length - first_part - len(ellipsis)):])
    return str


# ------------------------------------------------------------------------
def get_singleton(template_key, cls=None, raise_exception=True):
    cls = cls or settings.FEINCMS_DEFAULT_PAGE_MODEL
    try:
        model = apps.get_model(*cls.split('.'))
        if not model:
            raise ImproperlyConfigured('Cannot load model "%s"' % cls)
        try:
            assert model._feincms_templates[template_key].singleton
        except AttributeError as e:
            raise ImproperlyConfigured(
                '%r does not seem to be a valid FeinCMS base class (%r)' % (
                    model,
                    e,
                )
            )
        except KeyError:
            raise ImproperlyConfigured(
                '%r is not a registered template for %r!' % (
                    template_key,
                    model,
                )
            )
        except AssertionError:
            raise ImproperlyConfigured(
                '%r is not a *singleton* template for %r!' % (
                    template_key,
                    model,
                )
            )
        try:
            return model._default_manager.get(template_key=template_key)
        except model.DoesNotExist:
            raise  # not yet created?
        except model.MultipleObjectsReturned:
            raise  # hmm, not exactly a singleton...
    except Exception:
        if raise_exception:
            raise
        else:
            return None


def get_singleton_url(template_key, cls=None, raise_exception=True):
    obj = get_singleton(template_key, cls, raise_exception)
    return obj.get_absolute_url() if obj else '#broken-link'

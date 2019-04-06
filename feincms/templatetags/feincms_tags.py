# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import logging

import django
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from feincms.utils import get_singleton, get_singleton_url


register = template.Library()
assignment_tag = (
    register.simple_tag if django.VERSION >= (1, 9)
    else register.assignment_tag
)


def _render_content(content, **kwargs):
    # Track current render level and abort if we nest too deep. Avoids
    # crashing in recursive page contents (eg. a page list that contains
    # itself or similar).
    request = kwargs.get('request')
    if request is not None:
        level = getattr(request, 'feincms_render_level', 0)
        if level > 10:
            logging.getLogger('feincms').error(
                'Refusing to render %r, render level is already %s' % (
                    content, level))
            return
        setattr(request, 'feincms_render_level', level + 1)

    r = content.render(**kwargs)

    if request is not None:
        level = getattr(request, 'feincms_render_level', 1)
        setattr(request, 'feincms_render_level', max(level - 1, 0))

    return r


@register.simple_tag(takes_context=True)
def feincms_render_region(context, feincms_object, region, request=None):
    """
    {% feincms_render_region feincms_page "main" request %}
    """
    if not feincms_object:
        return ''

    return mark_safe(''.join(
        _render_content(content, request=request, context=context)
        for content in getattr(feincms_object.content, region)))


@register.simple_tag(takes_context=True)
def feincms_render_content(context, content, request=None):
    """
    {% feincms_render_content content request %}
    """
    if not content:
        return ''

    return _render_content(content, request=request, context=context)


@assignment_tag
def feincms_load_singleton(template_key, cls=None):
    """
    {% feincms_load_singleton template_key %} -- return a FeinCMS
    Base object which uses a Template with singleton=True.
    """
    return get_singleton(template_key, cls, raise_exception=settings.DEBUG)


@register.simple_tag
def feincms_singleton_url(template_key, cls=None):
    """
    {% feincms_singleton_url template_key %} -- return the URL of a FeinCMS
    Base object which uses a Template with singleton=True.
    """
    return get_singleton_url(template_key, cls, raise_exception=settings.DEBUG)

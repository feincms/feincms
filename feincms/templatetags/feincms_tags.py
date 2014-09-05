# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import logging

from django import template
from django.conf import settings
from django.template.loader import render_to_string

from feincms._internal import get_permission_codename
from feincms.utils import get_singleton, get_singleton_url


register = template.Library()


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

    if (request and request.COOKIES.get('frontend_editing', False)
            and hasattr(content, 'fe_render')):
        r = content.fe_render(**kwargs)
    else:
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
    return ''.join(
        _render_content(content, request=request, context=context)
        for content in getattr(feincms_object.content, region))


@register.simple_tag(takes_context=True)
def feincms_render_content(context, content, request=None):
    """
    {% feincms_render_content content request %}
    """
    return _render_content(content, request=request, context=context)


@register.simple_tag
def feincms_frontend_editing(cms_obj, request):
    """
    {% feincms_frontend_editing feincms_page request %}
    """

    if (hasattr(request, 'COOKIES')
            and request.COOKIES.get('frontend_editing') == 'True'):
        context = template.RequestContext(request, {
            "feincms_page": cms_obj,
        })
        return render_to_string('admin/feincms/fe_tools.html', context)

    return ''


@register.inclusion_tag('admin/feincms/content_type_selection_widget.html',
                        takes_context=True)
def show_content_type_selection_widget(context, region):
    """
    {% show_content_type_selection_widget region %}
    """
    if 'request' in context:
        user = context['request'].user
    elif 'user' in context:
        user = context['user']
    else:
        user = None

    grouped = {}
    ungrouped = []

    if user:
        for ct in region._content_types:
            # Skip cts that we shouldn't be adding anyway
            opts = ct._meta
            perm = opts.app_label + "." + get_permission_codename('add', opts)
            if not user.has_perm(perm):
                continue

            ct_info = (ct.__name__.lower(), ct._meta.verbose_name)
            if hasattr(ct, 'optgroup'):
                if ct.optgroup in grouped:
                    grouped[ct.optgroup].append(ct_info)
                else:
                    grouped[ct.optgroup] = [ct_info]
            else:
                ungrouped.append(ct_info)

    return {'grouped': grouped, 'ungrouped': ungrouped}


@register.assignment_tag
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

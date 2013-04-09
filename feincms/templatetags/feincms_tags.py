# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import logging

from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model
from django.template.loader import render_to_string

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

    if (request and request.COOKIES.get('frontend_editing', False) and\
            hasattr(content, 'fe_render')):
        r = content.fe_render(**kwargs)
    else:
        r = content.render(**kwargs)

    if request is not None:
        level = getattr(request, 'feincms_render_level', 1)
        setattr(request, 'feincms_render_level', max(level - 1, 0))

    return r


@register.simple_tag(takes_context=True)
def feincms_render_region(context, feincms_object, region, request):
    """
    {% feincms_render_region feincms_page "main" request %}
    """
    return u''.join(_render_content(content, request=request, context=context)
        for content in getattr(feincms_object.content, region))


@register.simple_tag(takes_context=True)
def feincms_render_content(context, content, request):
    """
    {% feincms_render_content content request %}
    """
    return _render_content(content, request=request, context=context)


@register.simple_tag
def feincms_frontend_editing(cms_obj, request):
    """
    {% feincms_frontend_editing feincms_page request %}
    """

    if hasattr(request, 'COOKIES') and request.COOKIES.get('frontend_editing') == 'True':
        context = template.RequestContext(request, {
            "feincms_page": cms_obj,
            })
        return render_to_string('admin/feincms/fe_tools.html', context)

    return u''

@register.inclusion_tag('admin/feincms/content_type_selection_widget.html', takes_context=True)
def show_content_type_selection_widget(context, region):
    """
    {% show_content_type_selection_widget region %}
    """
    grouped = {}
    ungrouped = []
    for ct in region._content_types:
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
def feincms_load_singleton(
        template_key,
        cls='page.Page',
        tag_name='feincms_load_singleton'
):
    """
    {% feincms_load_singleton template_key %} -- return a FeinCMS
    Base object which uses a Template with singleton=True.
    """
    try:
        model = get_model(*cls.split('.'))
        if not model:
            raise ImproperlyConfigured(
                u'{%% %s %%}: cannot load model "%s"' % (tag_name, cls)
            )
        try:
            assert model._feincms_templates[template_key].singleton
        except AttributeError, e:
            raise ImproperlyConfigured(
                u'{%% %s %%}: %r does not seem to be a '
                r'valid FeinCMS base class (%r)' % (tag_name, model, e)
            )
        except KeyError:
            raise ImproperlyConfigured(
                u'{%% %s %r %%}: not a registered template '
                r'for %r!' % (tag_name, template_key, model)
            )
        except AssertionError:
            raise ImproperlyConfigured(
                u'{%% %s %r %%}: not a singleton template '
                r'for %r!' % (tag_name, template_key, model)
            )
        try:
            return model._default_manager.get(template_key=template_key)
        except model.DoesNotExist:
            raise # not yet created?
        except model.MultipleObjectsReturned:
            raise # hmm, not exactly a singleton...
    except Exception:
        if settings.DEBUG:
            raise
        else:
            return None


@register.simple_tag
def feincms_singleton_url(template_key, cls='page.Page'):
    """
    {% feincms_singleton_url template_key %} -- return the URL of a FeinCMS
    Base object which uses a Template with singleton=True.
    """
    try:
        obj = feincms_load_singleton(
            template_key, cls=cls, tag_name='feincms_singleton_url')
        return obj.get_absolute_url()
    except Exception:
        if settings.DEBUG:
            raise
        else:
            return '#broken-link'

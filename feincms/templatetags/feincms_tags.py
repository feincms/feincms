# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from django import template
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
            # TODO: Log this
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

    if hasattr(request, 'session') and request.session.get('frontend_editing'):
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

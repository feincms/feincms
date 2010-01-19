from django import template
from django.template.loader import render_to_string
from feincms import settings as feincms_settings

from feincms import utils


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

    try:
        r = content.fe_render(**kwargs)
    except AttributeError:
        r = content.render(**kwargs)

    if request is not None:
        level = getattr(request, 'feincms_render_level', 1)
        setattr(request, 'feincms_render_level', max(level - 1, 0))

    return r

@register.simple_tag
def feincms_render_region(page, region, request, content_class=None):
    """
    {% feincms_render_region feincms_page "main" request %}
    """

    contents = getattr(page.content, region)

    if content_class:
        contents = [ c for c in contents if isinstance(c, content_class) ]

    return u''.join(_render_content(content, request=request) for content in contents)


@register.simple_tag
def feincms_render_content(content, request):
    """
    {% feincms_render_content contentblock request %}
    """

    return _render_content(content, request=request)


@register.simple_tag
def feincms_prefill_entry_list(queryset, attrs, region=None):
    """
    {% feincms_prefill_entry_list queryset "authors,richtextcontent_set" [region] %}
    """

    queryset = utils.prefill_entry_list(queryset, region=region, *(attrs.split(',')))
    return u''



@register.simple_tag
def feincms_frontend_editing(cms_obj, request):
    """
    {% feincms_frontend_editing feincms_page request %}
    """

    if hasattr(request, 'session') and request.session.get('frontend_editing'):
        ctx = template.RequestContext(request, {
            "feincms_page": cms_obj,
            'FEINCMS_ADMIN_MEDIA': feincms_settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': feincms_settings.FEINCMS_ADMIN_MEDIA_HOTLINKING
            })
        return render_to_string('admin/feincms/fe_tools.html', ctx)

    return u''

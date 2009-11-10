from django import template
from django.template.loader import render_to_string

from feincms import utils


register = template.Library()


def _render_content(content, **kwargs):
    try:
        return content.fe_render(**kwargs)
    except AttributeError:
        return content.render(**kwargs)


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
        return render_to_string('admin/feincms/fe_tools.html')

    return u''

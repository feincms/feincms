from django import template
from feincms import utils
from feincms.module.page.models import Page

register = template.Library()


@register.simple_tag
def feincms_render_region(page, region, request):
    """
    {% feincms_render_region feincms_page "main" request %}
    """

    contents = getattr(page.content, region)

    return u''.join(content.render(request=request) for content in contents)


@register.simple_tag
def feincms_render_content(content, request):
    """
    {% feincms_render_content contentblock request %}
    """

    return content.render(request=request)


@register.simple_tag
def feincms_prefill_entry_list(entry_list, attrs):
    """
    {% feincms_prefill_entry_list queryset "authors,richtextcontent_set" %}
    """

    queryset = utils.prefill_entry_list(queryset, *(attrs.split(',')))
    return u''



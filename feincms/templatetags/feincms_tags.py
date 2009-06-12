from django import template
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
    {% feincms_render_content pagecontent request %}
    """

    return content.render(request=request)


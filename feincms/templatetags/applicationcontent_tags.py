from django import template

# backwards compatibility import
from feincms.templatetags.fragment_tags import fragment, get_fragment, has_fragment

register = template.Library()

register.tag(fragment)
register.tag(get_fragment)
register.tag(has_fragment)


@register.simple_tag
def feincms_render_region_appcontent(page, region, request):
    """Render only the application content for the region

    This allows template authors to choose whether their page behaves
    differently when displaying embedded application subpages by doing
    something like this::

        {% if not in_appcontent_subpage %}
            {% feincms_render_region feincms_page "main" request %}
        {% else %}
            {% feincms_render_region_appcontent feincms_page "main" request %}
        {% endif %}
    """
    from feincms.content.application.models import ApplicationContent
    from feincms.templatetags.feincms_tags import _render_content

    return u''.join(_render_content(content, request=request) for content in\
        getattr(page.content, region) if isinstance(content, ApplicationContent))

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


class RenderRegionNode(template.Node):
    def __init__(self, feincms_object, region, request):
        self.feincms_object = template.Variable(feincms_object)
        self.region = template.Variable(region)
        self.request = template.Variable(request)

    def render(self, context):
        feincms_object = self.feincms_object.resolve(context)
        region = self.region.resolve(context)
        request = self.request.resolve(context)

        return u''.join(_render_content(content, request=request, context=context)\
            for content in getattr(feincms_object.content, region))


@register.tag
def feincms_render_region(parser, token):
    """
    {% feincms_render_region feincms_page "main" request %}
    """
    try:
        tag_name, feincms_object, region, request = token.contents.split()
    except ValueError:
        raise template.TemplateSyntaxError, 'Invalid syntax for feincms_render_region: %s' % token.contents

    return RenderRegionNode(feincms_object, region, request)
class CheckContentType(template.Node):
    def __init__(self, content, type2proof, var_name):
        self.content = content
        self.type2proof = type2proof
        self.var_name = var_name

    def render(self, context):
        #print context[self.content].__class__.__name__
        context[self.var_name] =context[self.content].__class__.__name__ == self.type2proof
        return ''
import re
@register.tag
def is_contenttype(parser, token):
       # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(\w+) (\w+) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    content, type2proof, var_name = m.groups()

    return CheckContentType(content, type2proof, var_name)

class RenderContentNode(template.Node):
    def __init__(self, content, request):
        self.content = template.Variable(content)
        self.request = template.Variable(request)

    def render(self, context):
        content = self.content.resolve(context)
        request = self.request.resolve(context)

        return _render_content(content, request=request, context=context)


@register.tag
def feincms_render_content(parser, token):
    """
    {% feincms_render_content contentblock request %}
    """
    try:
        tag_name, content, request = token.contents.split()
    except ValueError:
        raise template.TemplateSyntaxError, 'Invalid syntax for feincms_render_content: %s' % token.contents

    return RenderContentNode(content, request)


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
        context = template.RequestContext(request, {
            "feincms_page": cms_obj,
            'FEINCMS_ADMIN_MEDIA': feincms_settings.FEINCMS_ADMIN_MEDIA,
            'FEINCMS_ADMIN_MEDIA_HOTLINKING': feincms_settings.FEINCMS_ADMIN_MEDIA_HOTLINKING
            })
        return render_to_string('admin/feincms/fe_tools.html', context)

    return u''
import urllib
@register.filter
def quote_url(url):
    return urllib.quote_plus(url.encode('utf8'))

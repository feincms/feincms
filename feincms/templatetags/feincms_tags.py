from django import template
from django.template.loader import render_to_string

from feincms import utils
import os
from django.conf import settings
from django.template.base import Node, TemplateSyntaxError, NodeList


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


class IfMediaExistsNode(Node):
    child_nodelists = ('nodelist_true')

    def __init__(self, var, nodelist_true, nodelist_false, extra):
        self.var = var
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.extra = extra

    def __repr__(self):
        return "<IfMediaExistsNode>"

    def render(self, context):
        val = self.var
        if not isinstance(self.var, unicode):
            val = self.var.resolve(context, True)
        val += ''.join(self.extra)
        if val and os.path.exists(os.path.join(settings.MEDIA_ROOT, val)):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)
    
@register.tag
def media_exists(parser, token):
    """
    Outputs the contents of the block if mediafile in argument exists.

    Examples::

        {% media_exists fm.file.name %}
            ...
        {% endmedia_exists %}

        {% media_exists "medialibrary/2012/08/food-as.mp4.ogv" %}
            ...
        {% else %}
            ...
        {% endmedia_exists %}
    """
    bits = list(token.split_contents())
    if len(bits) < 2:
        raise TemplateSyntaxError("%r takes at least two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
        
    val = bits[1]
    if not bits[1].startswith('"') or not bits[1].endswith('"'): 
        val = parser.compile_filter(val)
    try:
        return IfMediaExistsNode(val, nodelist_true, nodelist_false, bits[2:])
    except IndexError:
        return IfMediaExistsNode(val, nodelist_true, nodelist_false, [])

@register.filter
def suffix_cutoff(value):
    return ''.join(value.split('.')[:-1])
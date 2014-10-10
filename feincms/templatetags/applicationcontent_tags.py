from __future__ import absolute_import, unicode_literals

from django import template
from django.core.urlresolvers import NoReverseMatch
from django.template import TemplateSyntaxError
from django.template.defaulttags import kwarg_re
from django.utils.encoding import smart_str

from feincms.apps import ApplicationContent, app_reverse as do_app_reverse
from feincms.templatetags.feincms_tags import _render_content
# backwards compatibility import
from feincms.templatetags.fragment_tags import (
    fragment, get_fragment, has_fragment)


register = template.Library()

register.tag(fragment)
register.tag(get_fragment)
register.filter(has_fragment)


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
    return ''.join(
        _render_content(content, request=request)
        for content in page.content.all_of_type(ApplicationContent)
        if content.region == region)


class AppReverseNode(template.Node):
    def __init__(self, view_name, urlconf, args, kwargs, asvar):
        self.view_name = view_name
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([
            (smart_str(k, 'ascii'), v.resolve(context))
            for k, v in self.kwargs.items()])
        view_name = self.view_name.resolve(context)
        urlconf = self.urlconf.resolve(context)

        try:
            url = do_app_reverse(
                view_name, urlconf, args=args, kwargs=kwargs,
                current_app=context.current_app)
        except NoReverseMatch:
            if self.asvar is None:
                raise
            url = ''

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url


@register.tag
def app_reverse(parser, token):
    """
    Returns an absolute URL for applications integrated with ApplicationContent

    The tag mostly works the same way as Django's own {% url %} tag::

        {% load applicationcontent_tags %}
        {% app_reverse "mymodel_detail" "myapp.urls" arg1 arg2 %}

        or

        {% load applicationcontent_tags %}
        {% app_reverse "mymodel_detail" "myapp.urls" name1=value1 %}

    The first argument is a path to a view. The second argument is the URLconf
    under which this app is known to the ApplicationContent. The second
    argument may also be a request object if you want to reverse an URL
    belonging to the current application content.

    Other arguments are space-separated values that will be filled in place of
    positional and keyword arguments in the URL. Don't mix positional and
    keyword arguments.

    If you want to store the URL in a variable instead of showing it right away
    you can do so too::

        {% app_reverse "mymodel_detail" "myapp.urls" arg1 arg2 as url %}
    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(
            "'%s' takes at least two arguments"
            " (path to a view and a urlconf)" % bits[0])
    viewname = parser.compile_filter(bits[1])
    urlconf = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None
    bits = bits[3:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError(
                    "Malformed arguments to app_reverse tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return AppReverseNode(viewname, urlconf, args, kwargs, asvar)

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


class NaviLevelNode(template.Node):
    """ Gets navigation based on current page OR request, dependant on choice of second parameter (of vs. from).

        Top navigation level is 1.
        If navigation level + 1 > page.level, the ouput is none, because there is no well-defined sub-sub-navigation for a page.

        Example usage:
        1) {% feincms_get_navi_level 1 of page as pages %}
        2) {% feincms_get_navi_level 1 from request as pages %}

        Side-note:  If not using mptt to retrieve pages, the ordering cannot be dertermined by 'id'.
        Instead, as a "hack", we can sort by field 'lft', because we understand how mptt works :-)
    """
    def __init__(self, level, switch, obj, dummy, varname):
        self.level = long(int(level) - 1)
        self.obj = template.Variable(obj)
        self.varname = varname
        self.switch = switch

    def render(self, context):
        if self.switch == 'of':
            # obj is a Page
            page = self.obj.resolve(context)
        else: # self.switch == 'from'
            # obj is a request
            page = Page.objects.from_request(self.obj.resolve(context))

        if int(self.level) == 0:
            # top level
            pages = Page.objects.filter(in_navigation=True, level=long(0)).order_by('lft')
        elif self.level <= page.level:
            ancestor = page.get_ancestors()[int(self.level) - 1]
            pages = Page.objects.filter(in_navigation=True, parent__pk=ancestor.pk).order_by('lft')
        elif self.level == page.level + 1:
            pages = Page.objects.filter(in_navigation=True, parent__pk=page.pk).order_by('lft')
        else:
            pages = []

        context[self.varname] = pages
        return ''

@register.tag
def feincms_get_navi_level(parser, token):
    try:
        tag_name, level, switch, obj, dummy, varname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly five arguments" % token.contents.split()[0]
    return NaviLevelNode(level, switch, obj, dummy, varname)


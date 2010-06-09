from django import template

register = template.Library()


class FragmentNode(template.Node):
    def __init__(self, nodelist, request, identifier, mode='append'):
        self.nodelist = nodelist
        self.request_var = template.Variable(request)
        self.identifier_var = template.Variable(identifier)
        self.mode = mode

    def render(self, context):
        request = self.request_var.resolve(context)
        identifier = self.identifier_var.resolve(context)
        rendered = self.nodelist.render(context)

        if not hasattr(request, '_feincms_fragments'):
            request._feincms_fragments = {}

        old = request._feincms_fragments.get(identifier, u'')

        if self.mode == 'prepend':
            request._feincms_fragments[identifier] = rendered + old
        elif self.mode == 'replace':
            request._feincms_fragments[identifier] = rendered
        else: # append
            request._feincms_fragments[identifier] = old + rendered

        return u''


@register.tag
def fragment(parser, token):
    """
    {% fragment request "title" %} content ... {% endfragment %}

    or

    {% fragment request "title" (prepend|replace|append) %} content ... {% endfragment %}
    """

    nodelist = parser.parse(('endfragment'),)
    parser.delete_first_token()

    return FragmentNode(nodelist, *token.contents.split()[1:])


class GetFragmentNode(template.Node):
    def __init__(self, request, fragment, as_var=None):
        self.request = template.Variable(request)
        self.fragment = template.Variable(fragment)
        self.as_var = as_var

    def render(self, context):
        request = self.request.resolve(context)
        fragment = self.fragment.resolve(context)

        try:
            value = request._feincms_fragments[fragment]
        except (AttributeError, KeyError):
            value = u''

        if self.as_var:
            context[self.as_var] = value
            return u''
        return value


@register.tag
def get_fragment(parser, token):
    """
    {% get_fragment request "title" %}
    or
    {% get_fragment request "title" as title %}
    """

    fragments = token.contents.split()

    if len(fragments) == 3:
        return GetFragmentNode(fragments[1], fragments[2])
    elif len(fragments) == 5 and fragments[3] == 'as':
        return GetFragmentNode(fragments[1], fragments[2], fragments[4])
    raise template.TemplateSyntaxError, 'Invalid syntax for get_fragment: %s' % token.contents


@register.filter
def has_fragment(request, identifier):
    """
    {% if request|has_fragment:"title" %}
    """
    return getattr(request, '_feincms_fragments', {}).get(identifier)

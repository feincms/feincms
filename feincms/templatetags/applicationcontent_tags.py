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


        old = request._feincms_applicationcontents_fragments.get(identifier, u'')

        if self.mode == 'prepend':
            request._feincms_applicationcontents_fragments[identifier] = rendered + old
        elif self.mode == 'replace':
            request._feincms_applicationcontents_fragments[identifier] = rendered
        else: # append
            request._feincms_applicationcontents_fragments[identifier] = old + rendered

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


@register.simple_tag
def get_fragment(request, identifier):
    """
    {% get_fragment request "title" %}
    """

    try:
        return request._feincms_applicationcontents_fragments[identifier]
    except (AttributeError, KeyError):
        return u''

'''
I really hate repeating myself. These are helpers that avoid typing the
whole thing over and over when implementing additional template tags

They help implementing tags of the following forms::

    {% tag as var_name %}
    {% tag of template_var as var_name %}
    {% tag of template_var as var_name arg1,arg2,kwarg3=4 %}
'''

from __future__ import absolute_import, unicode_literals

from django import template


def _parse_args(argstr, context=None):
    try:
        args = {}
        for token in argstr.split(','):
            if '=' in token:
                k, v = token.split('=', 1)
                if context:
                    try:
                        args[k] = template.Variable(v).resolve(context)
                    except template.VariableDoesNotExist:
                        args[k] = v
                else:
                    args[k] = v
            else:
                args[token] = True

        return args

    except TypeError:
        raise template.TemplateSyntaxError('Malformed arguments')


def do_simple_assignment_node_with_var_and_args_helper(cls):
    def _func(parser, token):
        try:
            tag_name, of_, in_var_name, as_, var_name, args =\
                token.contents.split()
        except ValueError:
            try:
                tag_name, of_, in_var_name, as_, var_name =\
                    token.contents.split()
                args = ''
            except ValueError:
                raise template.TemplateSyntaxError(
                    'Invalid syntax for %s node: %s' % (
                        cls.__name__, token.contents))

        return cls(tag_name, in_var_name, var_name, args)

    return _func


class SimpleAssignmentNodeWithVarAndArgs(template.Node):
    def __init__(self, tag_name, in_var_name, var_name, args):
        self.tag_name = tag_name
        self.in_var = template.Variable(in_var_name)
        self.var_name = var_name
        self.args = args

    def render(self, context):
        self.render_context = context
        try:
            instance = self.in_var.resolve(context)
        except template.VariableDoesNotExist:
            context[self.var_name] = []
            return ''

        context[self.var_name] = self.what(
            instance, _parse_args(self.args, context))

        return ''

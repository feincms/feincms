from django import template
from feincms.module.page.models import Page
from feincms.templatetags.utils import *

register = template.Library()


class NavigationNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    Example:
    {% feincms_navigation of feincms_page as sublevel level=2 %}
    {% for p in sublevel %}
        <a href="{{ p.get_absolute_url }}">{{ p.title }}</a>
    {% endfor %}
    """

    def what(self, instance, args):
        level = int(args.get('level', 1))

        if level <= 1:
            return Page.objects.toplevel_navigation()

        # mptt starts counting at 0, NavigationNode at 1; if we need the submenu
        # of the current page, we have to add 2 to the mptt level
        if instance.level+2 == level:
            return instance.children.in_navigation()

        try:
            return instance.get_ancestors()[level-2].children.in_navigation()
        except IndexError:
            return []
register.tag('feincms_navigation', do_simple_assignment_node_with_var_and_args_helper(NavigationNode))


class ParentLinkNode(SimpleNodeWithVarAndArgs):
    """
    {% feincms_parentlink of feincms_page level=1 %}
    """

    def what(self, page, args):
        level = int(args.get('level', 1))

        if page.level+1 == level:
            return page.get_absolute_url()
        elif page.level+1 < level:
            return '#'

        try:
            return page.get_ancestors()[level-1].get_absolute_url()
        except IndexError:
            return '#'
register.tag('feincms_parentlink', do_simple_node_with_var_and_args_helper(ParentLinkNode))


class BestMatchNode(SimpleAssignmentNodeWithVar):
    """
    {% feincms_bestmatch for request.path as feincms_page %}
    """

    def what(self, path):
        return Page.objects.best_match_for_path(path)
register.tag('feincms_bestmatch', do_simple_assignment_node_with_var_helper(BestMatchNode))


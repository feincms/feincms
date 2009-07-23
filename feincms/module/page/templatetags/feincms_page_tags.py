from django import template
from django.conf import settings
from django.http import HttpRequest

from feincms.module.page.models import Page, PageManager
from feincms.templatetags.utils import *

register = template.Library()


class NavigationNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    Return a list of pages to be used for the navigation

    level: 1 = toplevel, 2 = sublevel, 3 = sub-sublevel
    depth: 1 = only one level, 2 = subpages too

    If you set depth to something else than 1, you might want to look into
    the tree_info template tag from the mptt_tags library.

    Example:
    {% feincms_navigation of feincms_page as sublevel level=2,depth=1 %}
    {% for p in sublevel %}
        <a href="{{ p.get_absolute_url }}">{{ p.title }}</a>
    {% endfor %}
    """

    def what(self, instance, args):
        level = int(args.get('level', 1))
        depth = int(args.get('depth', 1))

        if isinstance(instance, HttpRequest):
            instance = Page.objects.from_request(instance)

        if level <= 1:
            if depth == 1:
                return Page.objects.toplevel_navigation()
            else:
                return Page.objects.in_navigation().filter(level__lt=depth)

        # mptt starts counting at 0, NavigationNode at 1; if we need the submenu
        # of the current page, we have to add 2 to the mptt level
        if instance.level + 2 == level:
            pass
        elif instance.level + 2 < level:
            try:
                queryset = instance.get_descendants().filter(level=level - 1, in_navigation=True)
                instance = PageManager.apply_active_filters(queryset)[0]
            except IndexError:
                return []
        else:
            instance = instance.get_ancestors()[level - 2]

        # special case for the navigation extension
        if getattr(instance, 'navigation_extension', None):
            # XXX what should be done with the depth parameter here?
            return instance.extended_navigation()
        else:
            if depth == 1:
                return instance.children.in_navigation()
            else:
                queryset = instance.get_descendants().filter(level__lte=instance.level + depth, in_navigation=True)
                return PageManager.apply_active_filters(queryset)
register.tag('feincms_navigation', do_simple_assignment_node_with_var_and_args_helper(NavigationNode))


class ParentLinkNode(SimpleNodeWithVarAndArgs):
    """
    {% feincms_parentlink of feincms_page level=1 %}
    """

    def what(self, page, args):
        level = int(args.get('level', 1))

        if page.level + 1 == level:
            return page.get_absolute_url()
        elif page.level + 1 < level:
            return '#'

        try:
            return page.get_ancestors()[level - 1].get_absolute_url()
        except IndexError:
            return '#'
register.tag('feincms_parentlink', do_simple_node_with_var_and_args_helper(ParentLinkNode))


class LanguageLinksNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    {% feincms_languagelinks for feincms_page as links [args] %}

    This template tag needs the translations extension.

    Arguments can be any combination of:
        all or existing: Return all languages or only those where a translation exists
        excludecurrent: Excludes the item in the current language from the list

    The default behavior is to return an entry for all languages including the
    current language.

    Example:

    {% feincms_languagelinks for entry as links all,excludecurrent %}
    {% for key, name, link in links %}
        <a href="{% if link %}{{ link }}{% else %}/{{ key }}/{% endif %}">{% trans name %}</a>
    {% endfor %}
    """

    def what(self, page, args):
        only_existing = args.get('existing', False)
        exclude_current = args.get('excludecurrent', False)

        translations = dict((t.language, t) for t in page.available_translations())
        translations[page.language] = page

        links = []
        for key, name in settings.LANGUAGES:
            if exclude_current and key == page.language:
                continue

            # hardcoded paths... bleh
            if key in translations:
                links.append((key, name, translations[key].get_absolute_url()))
            elif not only_existing:
                links.append((key, name, None))

        return links
register.tag('feincms_languagelinks', do_simple_assignment_node_with_var_and_args_helper(LanguageLinksNode))


@register.simple_tag
def feincms_breadcrumbs(page):
    """
    {% feincms_breadcrumbs feincms_page %}
    """
    ancs = page.get_ancestors()
    if not ancs:
        return ""
    bc = []
    for anc in ancs:
        bc.append('<a href="%s">%s</a> &gt; ' % (anc.get_absolute_url(), anc.title))
    bc.append(page.title)
    return "".join(bc)


@register.filter
def is_parent_of(page1, page2):
    """
    Determines whether a given page is the parent of another page

    Example:

    {% if page|is_parent_of:feincms_page %} ... {% endif %}
    """

    return page1.tree_id == page2.tree_id and page1.lft < page2.lft and page1.rght > page2.rght

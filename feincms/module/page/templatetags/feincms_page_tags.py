# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import warnings

from django import template
from django.conf import settings
from django.db.models import Q
from django.http import HttpRequest

from feincms.module.page.models import Page, PageManager
from feincms.utils.templatetags import *
from feincms.utils.templatetags import _parse_args

register = template.Library()


# ------------------------------------------------------------------------
@register.assignment_tag(takes_context=True)
def feincms_nav(context, feincms_page, level=1, depth=1):
    """
    New, simplified version of the ``{% feincms_navigation %}`` template tag.

    Generally we don't like abbreviations too much, but the similarity with
    the HTML5 <nav> tag was just too tempting.
    """

    if isinstance(feincms_page, HttpRequest):
        feincms_page = Page.objects.for_request(feincms_page, best_match=True)

    mptt_opts = feincms_page._mptt_meta

    # mptt starts counting at zero
    mptt_level_range = [level - 1, level + depth - 1]

    queryset = Page.objects.in_navigation().filter(**{
        '%s__gte' % mptt_opts.level_attr: mptt_level_range[0],
        '%s__lt' % mptt_opts.level_attr: mptt_level_range[1],
        })

    page_level = getattr(feincms_page, mptt_opts.level_attr)

    # Used for subset filtering (level>1)
    parent = None

    if level > 1:
        # A subset of the pages is requested. Determine it depending
        # upon the passed page instance

        if level - 2 == page_level:
            # The requested pages start directly below the current page
            parent = feincms_page

        elif level - 2 < page_level:
            # The requested pages start somewhere higher up in the tree
            parent = feincms_page.get_ancestors()[level - 2]

        if parent:
            # Special case for navigation extensions
            if getattr(parent, 'navigation_extension', None):
                return parent.extended_navigation(depth=depth,
                    request=context.get('request'))
            queryset &= parent.get_descendants()

    if depth > 1:
        # Filter out children with inactive parents
        # None (no parent) is always allowed
        parents = set([None])
        if parent:
            # Subset filtering; allow children of parent as well
            parents.add(parent.id)

        def _filter(iterable):
            for elem in iterable:
                if elem.parent_id in parents:
                    yield elem
                parents.add(elem.id)

        queryset = _filter(queryset)

    if 'navigation' in feincms_page._feincms_extensions:
        # Filter out children of nodes which have a navigation extension
        extended_node_rght = [] # mptt node right value

        def _filter(iterable):
            for elem in iterable:
                if extended_node_rght:
                    if getattr(elem, mptt_opts.right_attr) < extended_node_rght[-1]:
                        # Still inside some navigation extension
                        continue
                    else:
                        extended_node_rght.pop()

                if getattr(elem, 'navigation_extension', None):
                    yield elem
                    extended_node_rght.append(getattr(elem, mptt_opts.right_attr))

                    for extended in elem.extended_navigation(depth=depth,
                            request=context.get('request')):
                        if getattr(extended, mptt_opts.level_attr, 0) < level + depth - 1:
                            yield extended

                else:
                    yield elem

        queryset = _filter(queryset)

    # Return a list, not a generator so that it can be consumed
    # several times in a template.
    return list(queryset)


# ------------------------------------------------------------------------
class NavigationNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    Return a list of pages to be used for the navigation

    level: 1 = toplevel, 2 = sublevel, 3 = sub-sublevel
    depth: 1 = only one level, 2 = subpages too
    extended: run navigation extension on returned pages, not only on top-level node

    If you set depth to something else than 1, you might want to look into
    the tree_info template tag from the mptt_tags library.

    Example::

        {% feincms_navigation of feincms_page as sublevel level=2,depth=1 %}
        {% for p in sublevel %}
            <a href="{{ p.get_absolute_url }}">{{ p.title }}</a>
        {% endfor %}
    """

    def what(self, instance, args):
        warnings.warn('feincms_navigation and feincms_navigation_extended have'
            ' been deprecated and will be removed in FeinCMS v1.8. Start using'
            ' the new, shiny and bug-free feincms_nav today!',
            DeprecationWarning, stacklevel=3)

        return feincms_nav(
            self.render_context,
            instance,
            level=int(args.get('level', 1)),
            depth=int(args.get('depth', 1)),
            )
register.tag('feincms_navigation',
    do_simple_assignment_node_with_var_and_args_helper(NavigationNode))

# ------------------------------------------------------------------------
class ExtendedNavigationNode(NavigationNode):
    def render(self, context):
        self.render_context = context
        try:
            instance = self.in_var.resolve(context)
        except template.VariableDoesNotExist:
            context[self.var_name] = []
            return ''

        context[self.var_name] = self.what(instance, _parse_args(self.args, context))

        return ''
register.tag('feincms_navigation_extended',
    do_simple_assignment_node_with_var_and_args_helper(ExtendedNavigationNode))

# ------------------------------------------------------------------------
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

# ------------------------------------------------------------------------
class LanguageLinksNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    ::

        {% feincms_languagelinks for feincms_page as links [args] %}

    This template tag needs the translations extension.

    Arguments can be any combination of:

    * all or existing: Return all languages or only those where a translation exists
    * excludecurrent: Excludes the item in the current language from the list
    * request=request: The current request object, only needed if you are using
      AppContents and need to append the "extra path"

    The default behavior is to return an entry for all languages including the
    current language.

    Example::

        {% feincms_languagelinks for entry as links all,excludecurrent %}
        {% for key, name, link in links %}
            <a href="{% if link %}{{ link }}{% else %}/{{ key }}/{% endif %}">{% trans name %}</a>
        {% endfor %}
    """

    def what(self, page, args):
        only_existing = args.get('existing', False)
        exclude_current = args.get('excludecurrent', False)

        # Preserve the trailing path when switching languages if extra_path
        # exists (this is mostly the case when we are working inside an
        # ApplicationContent-managed page subtree)
        trailing_path = u''
        request = args.get('request', None)
        if request:
            # Trailing path without first slash
            trailing_path = request._feincms_extra_context.get('extra_path', '')[1:]

        translations = dict((t.language, t) for t in page.available_translations())
        translations[page.language] = page

        links = []
        for key, name in settings.LANGUAGES:
            if exclude_current and key == page.language:
                continue

            # hardcoded paths... bleh
            if key in translations:
                links.append((key, name, translations[key].get_absolute_url()+trailing_path))
            elif not only_existing:
                links.append((key, name, None))

        return links
register.tag('feincms_languagelinks', do_simple_assignment_node_with_var_and_args_helper(LanguageLinksNode))

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def _translate_page_into(page, language, default=None):
    """
    Return the translation for a given page
    """
    # Optimisation shortcut: No need to dive into translations if page already what we want
    try:
        if page.language == language:
            return page

        if language is not None:
            translations = dict((t.language, t) for t in page.available_translations())
            if language in translations:
                return translations[language]
    except AttributeError:
        pass

    if hasattr(default, '__call__'):
        return default(page=page)
    return default

# ------------------------------------------------------------------------
class TranslatedPageNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    ::

        {% feincms_translatedpage for feincms_page as feincms_transpage language=en %}
        {% feincms_translatedpage for feincms_page as originalpage %}
        {% feincms_translatedpage for some_page as translatedpage language=feincms_page.language %}

    This template tag needs the translations extension.

    Returns the requested translation of the page if it exists. If the language
    argument is omitted the primary language will be returned (the first language
    specified in settings.LANGUAGES).

    Note: To distinguish between a bare language code and a variable we check whether
    settings LANGUAGES contains that code -- so naming a variable "en" will probably
    not do what is intended.
    """
    def what(self, page, args, default=None):
        language = args.get('language', None)

        if language is None:
            language = settings.LANGUAGES[0][0]
        else:
            if language not in (x[0] for x in settings.LANGUAGES):
                try:
                    language = template.Variable(language).resolve(self.render_context)
                except template.VariableDoesNotExist:
                    language = settings.LANGUAGES[0][0]

        return _translate_page_into(page, language, default=default)
register.tag('feincms_translatedpage', do_simple_assignment_node_with_var_and_args_helper(TranslatedPageNode))

# ------------------------------------------------------------------------
class TranslatedPageNodeOrBase(TranslatedPageNode):
    def what(self, page, args):
        return super(TranslatedPageNodeOrBase, self).what(page, args, default=getattr(page, 'get_original_translation', page))
register.tag('feincms_translatedpage_or_base', do_simple_assignment_node_with_var_and_args_helper(TranslatedPageNodeOrBase))

# ------------------------------------------------------------------------
@register.filter
def feincms_translated_or_base(pages, language=None):
    if not hasattr(pages, '__iter__'):
        pages = [ pages ]
    for page in pages:
        yield _translate_page_into(page, language, default=page.get_original_translation)

# ------------------------------------------------------------------------
@register.inclusion_tag("breadcrumbs.html")
def feincms_breadcrumbs(page, include_self=True):
    """
    Generate a list of the page's ancestors suitable for use as breadcrumb navigation.

    By default, generates an unordered list with the id "breadcrumbs" -
    override breadcrumbs.html to change this.

    ::

        {% feincms_breadcrumbs feincms_page %}
    """

    if not page or not isinstance(page, Page):
        raise ValueError("feincms_breadcrumbs must be called with a valid Page object")

    ancs = page.get_ancestors()

    bc = [(anc.get_absolute_url(), anc.short_title()) for anc in ancs]

    if include_self:
        bc.append((None, page.short_title()))

    return {"trail": bc}

# ------------------------------------------------------------------------
def _is_parent_of(page1, page2):
    return page1.tree_id == page2.tree_id and page1.lft < page2.lft and page1.rght > page2.rght

@register.filter
def is_parent_of(page1, page2):
    """
    Determines whether a given page is the parent of another page

    Example::

        {% if page|is_parent_of:feincms_page %} ... {% endif %}
    """

    try:
        return _is_parent_of(page1, page2)
    except AttributeError:
        return False

# ------------------------------------------------------------------------
def _is_equal_or_parent_of(page1, page2):
    return page1.tree_id == page2.tree_id and page1.lft <= page2.lft and page1.rght >= page2.rght

@register.filter
def is_equal_or_parent_of(page1, page2):
    """
    Determines whether a given page is equal to or the parent of another
    page. This is especially handy when generating the navigation. The following
    example adds a CSS class ``current`` to the current main navigation entry::

        {% for page in navigation %}
            <a {% if page|is_equal_or_parent_of:feincms_page %}class="current"{% endif %}>
                {{ page.title }}</a>
        {% endfor %}
    """
    try:
        return _is_equal_or_parent_of(page1, page2)
    except AttributeError:
        return False

# ------------------------------------------------------------------------
def _is_sibling_of(page1, page2):
    return page1.parent_id == page2.parent_id

@register.filter
def is_sibling_of(page1, page2):
    """
    Determines whether a given page is a sibling of another page

    ::

        {% if page|is_sibling_of:feincms_page %} ... {% endif %}
    """

    try:
        return _is_sibling_of(page1, page2)
    except AttributeError:
        return False

# ------------------------------------------------------------------------
@register.filter
def siblings_along_path_to(page_list, page2):
    """
    Filters a list of pages so that only those remain that are either:

        * An ancestor of the current page
        * A sibling of an ancestor of the current page

    A typical use case is building a navigation menu with the active
    path to the current page expanded::

        {% feincms_nav feincms_page level=1 depth=3 as navitems %}
        {% with navitems|siblings_along_path_to:feincms_page as navtree %}
            ... whatever ...
        {% endwith %}

    """
    if page_list:
        try:
            # Try to avoid hitting the database: If the current page is in_navigation,
            # then all relevant pages are already in the incoming list, no need to
            # fetch ancestors or children.

            # NOTE: This assumes that the input list actually is complete (ie. comes from
            # feincms_nav). We'll cope with the fall-out of that assumption
            # when it happens...
            ancestors = [a_page for a_page in page_list
                                    if _is_equal_or_parent_of(a_page, page2)]
            top_level = min((a_page.level for a_page in page_list))

            if not ancestors:
                # Happens when we sit on a page outside the navigation tree
                # so fake an active root page to avoid a get_ancestors() db call
                # which would only give us a non-navigation root page anyway.
                p = Page(title="dummy", tree_id=-1, parent_id=None, in_navigation=False)
                ancestors = (p,)

            siblings  = [a_page for a_page in page_list
                                if a_page.parent_id == page2.id or
                                   a_page.level == top_level or
                                   any((_is_sibling_of(a_page, a) for a in ancestors))]
            return siblings
        except AttributeError:
            pass

    return ()

# ------------------------------------------------------------------------

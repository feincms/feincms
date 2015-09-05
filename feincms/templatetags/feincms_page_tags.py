# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

import logging
import sys
import traceback

from django import template
from django.apps import apps
from django.conf import settings
from django.http import HttpRequest

from feincms import settings as feincms_settings
from feincms.module.page.extensions.navigation import PagePretender
from feincms.utils.templatetags import (
    SimpleAssignmentNodeWithVarAndArgs,
    do_simple_assignment_node_with_var_and_args_helper)


logger = logging.getLogger('feincms.templatetags.page')

register = template.Library()


def _get_page_model():
    return apps.get_model(
        *feincms_settings.FEINCMS_DEFAULT_PAGE_MODEL.split('.'))


# ------------------------------------------------------------------------
# TODO: Belongs in some utility module
def format_exception(e):
    top = traceback.extract_tb(sys.exc_info()[2])[-1]
    return "'%s' in %s line %d" % (e, top[0], top[1])


# ------------------------------------------------------------------------
@register.assignment_tag(takes_context=True)
def feincms_nav(context, feincms_page, level=1, depth=1, group=None):
    """
    Saves a list of pages into the given context variable.
    """

    page_class = _get_page_model()

    if not feincms_page:
        return []

    if isinstance(feincms_page, HttpRequest):
        try:
            feincms_page = page_class.objects.for_request(
                feincms_page, best_match=True)
        except page_class.DoesNotExist:
            return []

    mptt_opts = feincms_page._mptt_meta

    # mptt starts counting at zero
    mptt_level_range = [level - 1, level + depth - 1]

    queryset = feincms_page.__class__._default_manager.in_navigation().filter(
        **{
            '%s__gte' % mptt_opts.level_attr: mptt_level_range[0],
            '%s__lt' % mptt_opts.level_attr: mptt_level_range[1],
        }
    )

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

        elif level - 1 > page_level:
            # The requested pages are grandchildren of the current page
            # (or even deeper in the tree). If we would continue processing,
            # this would result in pages from different subtrees being
            # returned directly adjacent to each other.
            queryset = page_class.objects.none()

        if parent:
            if getattr(parent, 'navigation_extension', None):
                # Special case for navigation extensions
                return list(parent.extended_navigation(
                    depth=depth, request=context.get('request')))

            # Apply descendant filter
            queryset &= parent.get_descendants()

    if depth > 1:
        # Filter out children with inactive parents
        # None (no parent) is always allowed
        parents = set([None])
        if parent:
            # Subset filtering; allow children of parent as well
            parents.add(parent.id)

        def _parentactive_filter(iterable):
            for elem in iterable:
                if elem.parent_id in parents:
                    yield elem
                parents.add(elem.id)

        queryset = _parentactive_filter(queryset)

    if group is not None:
        # navigationgroups extension support
        def _navigationgroup_filter(iterable):
            for elem in iterable:
                if getattr(elem, 'navigation_group', None) == group:
                    yield elem

        queryset = _navigationgroup_filter(queryset)

    if hasattr(feincms_page, 'navigation_extension'):
        # Filter out children of nodes which have a navigation extension
        def _navext_filter(iterable):
            current_navextension_node = None
            for elem in iterable:
                # Eliminate all subitems of last processed nav extension
                if current_navextension_node is not None and \
                   current_navextension_node.is_ancestor_of(elem):
                    continue

                yield elem
                if getattr(elem, 'navigation_extension', None):
                    current_navextension_node = elem
                    try:
                        for extended in elem.extended_navigation(
                                depth=depth, request=context.get('request')):
                            # Only return items from the extended navigation
                            # which are inside the requested level+depth
                            # values. The "-1" accounts for the differences in
                            # MPTT and navigation level counting
                            this_level = getattr(
                                extended, mptt_opts.level_attr, 0)
                            if this_level < level + depth - 1:
                                yield extended
                    except Exception as e:
                        logger.warn(
                            "feincms_nav caught exception in navigation"
                            " extension for page %d: %s",
                            current_navextension_node.id, format_exception(e))
                else:
                    current_navextension_node = None

        queryset = _navext_filter(queryset)

    # Return a list, not a generator so that it can be consumed
    # several times in a template.
    return list(queryset)


# ------------------------------------------------------------------------
class LanguageLinksNode(SimpleAssignmentNodeWithVarAndArgs):
    """
    ::

        {% feincms_languagelinks for feincms_page as links [args] %}

    This template tag needs the translations extension.

    Arguments can be any combination of:

    * all or existing: Return all languages or only those where a translation
      exists
    * excludecurrent: Excludes the item in the current language from the list
    * request=request: The current request object, only needed if you are using
      AppContents and need to append the "extra path"

    The default behavior is to return an entry for all languages including the
    current language.

    Example::

      {% feincms_languagelinks for feincms_page as links all,excludecurrent %}
      {% for key, name, link in links %}
          <a href="{% if link %}{{ link }}{% else %}/{{ key }}/{% endif %}">
            {% trans name %}</a>
      {% endfor %}
    """

    def what(self, page, args):
        only_existing = args.get('existing', False)
        exclude_current = args.get('excludecurrent', False)

        # Preserve the trailing path when switching languages if extra_path
        # exists (this is mostly the case when we are working inside an
        # ApplicationContent-managed page subtree)
        trailing_path = ''
        request = args.get('request', None)
        if request:
            # Trailing path without first slash
            trailing_path = request._feincms_extra_context.get(
                'extra_path', '')[1:]

        translations = dict(
            (t.language, t) for t in page.available_translations())
        translations[page.language] = page

        links = []
        for key, name in settings.LANGUAGES:
            if exclude_current and key == page.language:
                continue

            # hardcoded paths... bleh
            if key in translations:
                links.append((
                    key,
                    name,
                    translations[key].get_absolute_url() + trailing_path))
            elif not only_existing:
                links.append((key, name, None))

        return links

register.tag(
    'feincms_languagelinks',
    do_simple_assignment_node_with_var_and_args_helper(LanguageLinksNode))


# ------------------------------------------------------------------------
def _translate_page_into(page, language, default=None):
    """
    Return the translation for a given page
    """
    # Optimisation shortcut: No need to dive into translations if page already
    # what we want
    try:
        if page.language == language:
            return page

        if language is not None:
            translations = dict(
                (t.language, t) for t in page.available_translations())
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

        {% feincms_translatedpage for feincms_page as feincms_transpage
            language=en %}
        {% feincms_translatedpage for feincms_page as originalpage %}
        {% feincms_translatedpage for some_page as translatedpage
            language=feincms_page.language %}

    This template tag needs the translations extension.

    Returns the requested translation of the page if it exists. If the language
    argument is omitted the primary language will be returned (the first
    language specified in settings.LANGUAGES).

    Note: To distinguish between a bare language code and a variable we check
    whether settings LANGUAGES contains that code -- so naming a variable "en"
    will probably not do what is intended.
    """
    def what(self, page, args, default=None):
        language = args.get('language', None)

        if language is None:
            language = settings.LANGUAGES[0][0]
        else:
            if language not in (x[0] for x in settings.LANGUAGES):
                try:
                    language = template.Variable(language).resolve(
                        self.render_context)
                except template.VariableDoesNotExist:
                    language = settings.LANGUAGES[0][0]

        return _translate_page_into(page, language, default=default)

register.tag(
    'feincms_translatedpage',
    do_simple_assignment_node_with_var_and_args_helper(TranslatedPageNode))


# ------------------------------------------------------------------------
class TranslatedPageNodeOrBase(TranslatedPageNode):
    def what(self, page, args):
        return super(TranslatedPageNodeOrBase, self).what(
            page, args,
            default=getattr(page, 'get_original_translation', page))

register.tag(
    'feincms_translatedpage_or_base',
    do_simple_assignment_node_with_var_and_args_helper(
        TranslatedPageNodeOrBase))


# ------------------------------------------------------------------------
@register.filter
def feincms_translated_or_base(pages, language=None):
    if not hasattr(pages, '__iter__'):
        pages = [pages]
    for page in pages:
        yield _translate_page_into(
            page, language, default=page.get_original_translation)


# ------------------------------------------------------------------------
@register.inclusion_tag("breadcrumbs.html")
def feincms_breadcrumbs(page, include_self=True):
    """
    Generate a list of the page's ancestors suitable for use as breadcrumb
    navigation.

    By default, generates an unordered list with the id "breadcrumbs" -
    override breadcrumbs.html to change this.

    ::

        {% feincms_breadcrumbs feincms_page %}
    """

    ancs = page.get_ancestors()

    bc = [(anc.get_absolute_url(), anc.short_title()) for anc in ancs]

    if include_self:
        bc.append((None, page.short_title()))

    return {"trail": bc}


# ------------------------------------------------------------------------
@register.filter
def is_parent_of(page1, page2):
    """
    Determines whether a given page is the parent of another page

    Example::

        {% if page|is_parent_of:feincms_page %} ... {% endif %}
    """

    try:
        return page1.is_ancestor_of(page2)
    except (AttributeError, ValueError):
        return False


# ------------------------------------------------------------------------
@register.filter
def is_equal_or_parent_of(page1, page2):
    """
    Determines whether a given page is equal to or the parent of another page.
    This is especially handy when generating the navigation. The following
    example adds a CSS class ``current`` to the current main navigation entry::

        {% for page in navigation %}
            <a
            {% if page|is_equal_or_parent_of:feincms_page %}
                class="current"
            {% endif %}
            >{{ page.title }}</a>
        {% endfor %}
    """
    try:
        return page1.is_ancestor_of(page2, include_self=True)
    except (AttributeError, ValueError):
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
            # Try to avoid hitting the database: If the current page is
            # in_navigation, then all relevant pages are already in the
            # incoming list, no need to fetch ancestors or children.

            # NOTE: This assumes that the input list actually is complete (ie.
            # comes from feincms_nav). We'll cope with the fall-out of that
            # assumption when it happens...
            ancestors = [
                a_page for a_page in page_list
                if a_page.is_ancestor_of(page2, include_self=True)]
            top_level = min((a_page.level for a_page in page_list))

            if not ancestors:
                # Happens when we sit on a page outside the navigation tree so
                # fake an active root page to avoid a get_ancestors() db call
                # which would only give us a non-navigation root page anyway.
                page_class = _get_page_model()

                p = page_class(
                    title="dummy",
                    tree_id=-1,
                    parent_id=None,
                    in_navigation=False)
                ancestors = (p,)

            siblings = [
                a_page for a_page in page_list if (
                    a_page.parent_id == page2.id or
                    a_page.level == top_level or
                    any((_is_sibling_of(a_page, a) for a in ancestors))
                )
            ]

            return siblings
        except (AttributeError, ValueError) as e:
            logger.warn(
                "siblings_along_path_to caught exception: %s",
                format_exception(e))

    return ()


# ------------------------------------------------------------------------
@register.assignment_tag(takes_context=True)
def page_is_active(context, page, feincms_page=None, path=None):
    """
    Usage example::

        {% feincms_nav feincms_page level=1 as toplevel %}
        <ul>
        {% for page in toplevel %}
            {% page_is_active page as is_active %}
            <li {% if is_active %}class="active"{% endif %}>
                <a href="{{ page.get_navigation_url }}">{{ page.title }}</a>
            <li>
        {% endfor %}
        </ul>
    """
    if isinstance(page, PagePretender):
        if path is None:
            path = context['request'].path_info
        return path.startswith(page.get_absolute_url())

    else:
        if feincms_page is None:
            feincms_page = context['feincms_page']
        return page.is_ancestor_of(feincms_page, include_self=True)

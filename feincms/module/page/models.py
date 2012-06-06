# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import re

from django.core.cache import cache as django_cache
from django.conf import settings as django_settings
from django.db import models
from django.db.models import Q, signals
from django.http import Http404
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.db.transaction import commit_on_success

from mptt.models import MPTTModel

from feincms import settings
from feincms.management.checker import check_database_schema
from feincms.models import create_base_model
from feincms.module.page import processors
from feincms.utils.managers import ActiveAwareContentManagerMixin

from feincms.utils import path_to_cache_key

# ------------------------------------------------------------------------
class PageManager(models.Manager, ActiveAwareContentManagerMixin):
    """
    The page manager. Only adds new methods, does not modify standard Django
    manager behavior in any way.
    """

    # The fields which should be excluded when creating a copy.
    exclude_from_copy = ['id', 'tree_id', 'lft', 'rght', 'level', 'redirect_to']

    def page_for_path(self, path, raise404=False):
        """
        Return a page for a path. Optionally raises a 404 error if requested.

        Example::

            Page.objects.page_for_path(request.path)
        """

        stripped = path.strip('/')

        try:
            return self.active().get(_cached_url=stripped and u'/%s/' % stripped or '/')
        except self.model.DoesNotExist:
            if raise404:
                raise Http404
            raise

    def best_match_for_path(self, path, raise404=False):
        """
        Return the best match for a path. If the path as given is unavailable,
        continues to search by chopping path components off the end.

        Tries hard to avoid unnecessary database lookups by generating all
        possible matching URL prefixes and choosing the longest match.

        Page.best_match_for_path('/photos/album/2008/09') might return the
        page with url '/photos/album/'.
        """

        paths = ['/']
        path = path.strip('/')

        # Cache path -> page resolving.
        # We flush the cache entry on page saving, so the cache should always
        # be up to date.

        ck = Page.path_to_cache_key(path)
        page = django_cache.get(ck)
        if page:
            return page

        if path:
            tokens = path.split('/')
            paths += ['/%s/' % '/'.join(tokens[:i]) for i in range(1, len(tokens)+1)]

        try:
            page = self.active().filter(_cached_url__in=paths).extra(
                select={'_url_length': 'LENGTH(_cached_url)'}).order_by('-_url_length')[0]
            django_cache.set(ck, page)
            return page
        except IndexError:
            if raise404:
                raise Http404

        raise self.model.DoesNotExist

    def in_navigation(self):
        """
        Returns active pages which have the ``in_navigation`` flag set.
        """

        return self.active().filter(in_navigation=True)

    def toplevel_navigation(self):
        """
        Returns top-level navigation entries.
        """

        return self.in_navigation().filter(parent__isnull=True)

    def for_request(self, request, raise404=False, best_match=False, setup=True):
        """
        Return a page for the request

        Does not hit the database more than once for the same request.

        Examples::

            Page.objects.for_request(request, raise404=True, best_match=False)

        Defaults to raising a ``DoesNotExist`` exception if no exact match
        could be determined.
        """

        if not hasattr(request, '_feincms_page'):
            path = request.path_info or request.path

            if best_match:
                request._feincms_page = self.best_match_for_path(path, raise404=raise404)
            else:
                request._feincms_page = self.page_for_path(path, raise404=raise404)

        if setup:
            request._feincms_page.setup_request(request)
        return request._feincms_page


PageManager.add_to_active_filters(Q(active=True))

# ------------------------------------------------------------------------
class Page(create_base_model(MPTTModel)):
    active = models.BooleanField(_('active'), default=True)

    # structure and navigation
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=150)
    parent = models.ForeignKey('self', verbose_name=_('Parent'), blank=True, null=True, related_name='children')
    parent.parent_filter = True # Custom list_filter - see admin/filterspecs.py
    in_navigation = models.BooleanField(_('in navigation'), default=True)
    override_url = models.CharField(_('override URL'), max_length=300, blank=True,
        help_text=_('Override the target URL. Be sure to include slashes at the beginning and at the end if it is a local URL. This affects both the navigation and subpages\' URLs.'))
    redirect_to = models.CharField(_('redirect to'), max_length=300, blank=True,
        help_text=_('Target URL for automatic redirects.'))
    _cached_url = models.CharField(_('Cached URL'), max_length=300, blank=True,
        editable=False, default='', db_index=True)

    request_processors = SortedDict()
    response_processors = SortedDict()
    cache_key_components = [ lambda p: django_settings.SITE_ID,
                             lambda p: p._django_content_type.id,
                             lambda p: p.id ]

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    objects = PageManager()

    def __unicode__(self):
        return self.short_title()

    def is_active(self):
        """
        Check whether this page and all its ancestors are active
        """

        if not self.pk:
            return False

        pages = Page.objects.active().filter(tree_id=self.tree_id, lft__lte=self.lft, rght__gte=self.rght)
        return pages.count() > self.level
    is_active.short_description = _('is active')

    def are_ancestors_active(self):
        """
        Check whether all ancestors of this page are active
        """

        if self.is_root_node():
            return True

        queryset = PageManager.apply_active_filters(self.get_ancestors())
        return queryset.count() >= self.level

    def short_title(self):
        """
        Title shortened for display.
        """
        from feincms.utils import shorten_string
        return shorten_string(self.title)
    short_title.admin_order_field = 'title'
    short_title.short_description = _('title')

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        # Cache a copy of the loaded _cached_url value so we can reliably
        # determine whether it has been changed in the save handler:
        self._original_cached_url = self._cached_url

    @commit_on_success
    def save(self, *args, **kwargs):
        """
        Overridden save method which updates the ``_cached_url`` attribute of
        this page and all subpages. Quite expensive when called with a page
        high up in the tree.
        """

        cached_page_urls = {}

        # determine own URL
        if self.override_url:
            self._cached_url = self.override_url
        elif self.is_root_node():
            self._cached_url = u'/%s/' % self.slug
        else:
            self._cached_url = u'%s%s/' % (self.parent._cached_url, self.slug)

        cached_page_urls[self.id] = self._cached_url
        super(Page, self).save(*args, **kwargs)

        # Okay, we changed the URL -- remove the old stale entry from the cache
        ck = self.path_to_cache_key(self._original_cached_url)
        django_cache.delete(ck)

        # If our cached URL changed we need to update all descendants to
        # reflect the changes. Since this is a very expensive operation
        # on large sites we'll check whether our _cached_url actually changed
        # or if the updates weren't navigation related:
        if self._cached_url == self._original_cached_url:
            return

        # TODO: Does not find everything it should when ContentProxy content
        # inheritance has been customized.
        pages = self.get_descendants().order_by('lft')

        for page in pages:
            if page.override_url:
                page._cached_url = page.override_url
            else:
                # cannot be root node by definition
                page._cached_url = u'%s%s/' % (
                    cached_page_urls[page.parent_id],
                    page.slug)

            cached_page_urls[page.id] = page._cached_url
            super(Page, page).save() # do not recurse

    @models.permalink
    def get_absolute_url(self):
        """
        Return the absolute URL of this page.
        """
        # result url never begins or ends with a slash
        url = self._cached_url.strip('/')
        if url:
            return ('feincms_handler', (url,), {})
        return ('feincms_home', (), {})

    def get_navigation_url(self):
        """
        Return either ``redirect_to`` if it is set, or the URL of this page.
        """

        return self.redirect_to or self._cached_url

    def cache_key(self):
        """
        Return a string that may be used as cache key for the current page.
        The cache_key is unique for each content type and content instance.
        """
        return '-'.join(unicode(fn(self)) for fn in self.cache_key_components)

    def etag(self, request):
        """
        Generate an etag for this page.
        An etag should be unique and unchanging for as long as the page
        content does not change. Since we have no means to determine whether
        rendering the page now (as opposed to a minute ago) will actually
        give the same result, this default implementation returns None, which
        means "No etag please, thanks for asking".
        """
        return None

    def last_modified(self, request):
        """
        Generate a last modified date for this page.
        Since a standard page has no way of knowing this, we always return
        "no date" -- this is overridden by the changedate extension.
        """
        return None

    def setup_request(self, request):
        """
        Before rendering a page, run all registered request processors. A request
        processor may peruse and modify the page or the request. It can also return
        a HttpResponse for shortcutting the page rendering and returning that response
        immediately to the client.

        ``setup_request`` stores responses returned by request processors and returns
        those on every subsequent call to ``setup_request``. This means that
        ``setup_request`` can be called repeatedly during the same request-response
        cycle without harm - request processors are executed exactly once.
        """

        if hasattr(self, '_setup_request_result'):
            return self._setup_request_result
        else:
            # Marker -- setup_request has been successfully run before
            self._setup_request_result = None

        if not hasattr(request, '_feincms_extra_context'):
            request._feincms_extra_context = {}

        request._feincms_extra_context.update({
            'in_appcontent_subpage': False, # XXX This variable name isn't accurate anymore.
                                            # We _are_ in a subpage, but it isn't necessarily
                                            # an appcontent subpage.
            'extra_path': '/',
            })

        url = self.get_absolute_url()
        if request.path != url:
            # extra_path must not end with a slash
            request._feincms_extra_context.update({
                'in_appcontent_subpage': True,
                'extra_path': re.sub('^' + re.escape(url.rstrip('/')), '',
                    request.path),
                })

        for fn in reversed(self.request_processors.values()):
            r = fn(self, request)
            if r:
                self._setup_request_result = r
                break

        return self._setup_request_result

    def finalize_response(self, request, response):
        """
        After rendering a page to a response, the registered response processors are
        called to modify the response, eg. for setting cache or expiration headers,
        keeping statistics, etc.
        """
        for fn in self.response_processors.values():
            fn(self, request, response)

    def get_redirect_to_target(self, request):
        """
        This might be overriden/extended by extension modules.
        """
        return self.redirect_to

    @classmethod
    def register_request_processor(cls, fn, key=None):
        """
        Registers the passed callable as request processor. A request processor
        always receives two arguments, the current page object and the request.
        """
        cls.request_processors[fn if key is None else key] = fn

    @classmethod
    def register_response_processor(cls, fn, key=None):
        """
        Registers the passed callable as response processor. A response processor
        always receives three arguments, the current page object, the request
        and the response.
        """
        cls.response_processors[fn if key is None else key] = fn

    @classmethod
    def register_extension(cls, register_fn):
        register_fn(cls, PageAdmin)

    @staticmethod
    def path_to_cache_key(path):
        return path_to_cache_key(path.strip('/'), prefix="PAGE-FOR-URL")

# ------------------------------------------------------------------------
# Our default request processors

Page.register_request_processor(processors.require_path_active_request_processor,
    key='path_active')
Page.register_request_processor(processors.redirect_request_processor,
    key='redirect')

if settings.FEINCMS_FRONTEND_EDITING:
    Page.register_request_processor(processors.frontendediting_request_processor,
        key='frontend_editing')

signals.post_syncdb.connect(check_database_schema(Page, __name__), weak=False)

# ------------------------------------------------------------------------
# Down here as to avoid circular imports
from .modeladmins import PageAdmin

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

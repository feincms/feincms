# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import re

from django.core.cache import cache as django_cache
from django.conf import settings as django_settings
from django.db import models
from django.db.models import Q, signals
from django.db.models.loading import get_model
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.db.transaction import commit_on_success

from mptt.models import MPTTModel

from feincms import settings
from feincms.management.checker import check_database_schema
from feincms.models import create_base_model
from feincms.module.mixins import ContentModelMixin
from feincms.module.page import processors
from feincms.utils.managers import ActiveAwareContentManagerMixin

from feincms.utils import path_to_cache_key


REDIRECT_TO_RE = re.compile(
    r'^(?P<app_label>\w+).(?P<module_name>\w+):(?P<pk>\d+)$')


# ------------------------------------------------------------------------
class BasePageManager(models.Manager, ActiveAwareContentManagerMixin):
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
            page = self.active().get(
                _cached_url=u'/%s/' % stripped if stripped else '/')

            if not page.are_ancestors_active():
                raise self.model.DoesNotExist('Parents are inactive.')

            return page

        except self.model.DoesNotExist:
            if raise404:
                raise Http404()
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

            if not page.are_ancestors_active():
                raise IndexError('Parents are inactive.')

            django_cache.set(ck, page)
            return page

        except IndexError:
            if raise404:
                raise Http404()

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

    def for_request(self, request, raise404=False, best_match=False,
            setup=False):
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
                request._feincms_page = self.best_match_for_path(path,
                    raise404=raise404)
            else:
                request._feincms_page = self.page_for_path(path,
                    raise404=raise404)

        if setup:
            import warnings
            warnings.warn(
                'Calling for_request with setup=True does nothing anymore.'
                ' The parameter will be removed in FeinCMS v1.8.',
                DeprecationWarning, stacklevel=2)

        return request._feincms_page

# ------------------------------------------------------------------------
class PageManager(BasePageManager):
    pass

PageManager.add_to_active_filters(Q(active=True))

# ------------------------------------------------------------------------
class BasePage(create_base_model(MPTTModel), ContentModelMixin):
    active = models.BooleanField(_('active'), default=True)

    # structure and navigation
    title = models.CharField(_('title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=150)
    parent = models.ForeignKey('self', verbose_name=_('Parent'), blank=True, null=True, related_name='children')
    parent.parent_filter = True # Custom list_filter - see admin/filterspecs.py
    in_navigation = models.BooleanField(_('in navigation'), default=True)
    override_url = models.CharField(_('override URL'), max_length=255, blank=True,
        help_text=_('Override the target URL. Be sure to include slashes at the beginning and at the end if it is a local URL. This affects both the navigation and subpages\' URLs.'))
    redirect_to = models.CharField(_('redirect to'), max_length=255, blank=True,
        help_text=_('Target URL for automatic redirects'
            ' or the primary key of a page.'))
    _cached_url = models.CharField(_('Cached URL'), max_length=255, blank=True,
        editable=False, default='', db_index=True)

    cache_key_components = [ lambda p: getattr(django_settings, 'SITE_ID', 0),
                             lambda p: p._django_content_type.id,
                             lambda p: p.id ]

    class Meta:
        ordering = ['tree_id', 'lft']
        abstract = True

    objects = PageManager()

    def __unicode__(self):
        return self.short_title()

    def is_active(self):
        """
        Check whether this page and all its ancestors are active
        """

        if not self.pk:
            return False

        pages = self.__class__.objects.active().filter(tree_id=self.tree_id, lft__lte=self.lft, rght__gte=self.rght)
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
        super(BasePage, self).__init__(*args, **kwargs)
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
        super(BasePage, self).save(*args, **kwargs)

        # Okay, we have changed the page -- remove the old stale entry from the cache
        self.invalidate_cache()

        # If our cached URL changed we need to update all descendants to
        # reflect the changes. Since this is a very expensive operation
        # on large sites we'll check whether our _cached_url actually changed
        # or if the updates weren't navigation related:
        if self._cached_url == self._original_cached_url:
            return

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
            super(BasePage, page).save() # do not recurse
    save.alters_data = True

    @commit_on_success
    def delete(self, *args, **kwargs):
        super(BasePage, self).delete(*args, **kwargs)
        self.invalidate_cache()
    delete.alters_data = True

    # Remove the page from the url-to-page cache
    def invalidate_cache(self):
        ck = self.path_to_cache_key(self._original_cached_url)
        django_cache.delete(ck)
        ck = self.path_to_cache_key(self._cached_url)
        django_cache.delete(ck)

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

        # :-( maybe this could be cleaned up a bit?
        if not self.redirect_to or REDIRECT_TO_RE.match(self.redirect_to):
            return self._cached_url
        return self.redirect_to

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

    def get_redirect_to_target(self, request):
        """
        This might be overriden/extended by extension modules.
        """

        if not self.redirect_to:
            return u''

        # It might be an identifier for a different object
        match = REDIRECT_TO_RE.match(self.redirect_to)

        # It's not, oh well.
        if not match:
            return self.redirect_to

        matches = match.groupdict()
        model = get_model(matches['app_label'], matches['module_name'])

        if not model:
            return self.redirect_to

        try:
            instance = model._default_manager.get(pk=int(matches['pk']))
            return instance.get_absolute_url()
        except models.ObjectDoesNotExist:
            pass

        return self.redirect_to

    @classmethod
    def path_to_cache_key(cls, path):
        prefix = "%s-FOR-URL" % cls.__name__.upper()
        return path_to_cache_key(path.strip('/'), prefix=prefix)

    @classmethod
    def register_default_processors(cls, frontend_editing=False):
        """
        Register our default request processors for the out-of-the-box
        Page experience.
        """
        cls.register_request_processor(processors.redirect_request_processor,
                                       key='redirect')
        cls.register_request_processor(processors.extra_context_request_processor,
                                       key='extra_context')

        if frontend_editing:
            cls.register_request_processor(processors.frontendediting_request_processor,
                                           key='frontend_editing')
            cls.register_response_processor(processors.frontendediting_response_processor,
                                            key='frontend_editing')

# ------------------------------------------------------------------------
class Page(BasePage):
    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

Page.register_default_processors(frontend_editing=settings.FEINCMS_FRONTEND_EDITING)

signals.post_syncdb.connect(check_database_schema(Page, __name__), weak=False)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

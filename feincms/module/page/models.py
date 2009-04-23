from django.conf import settings
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

import mptt

from feincms.models import TypeRegistryMetaClass, Region, Template,\
    Base, ContentProxy


def get_object(path, fail_silently=False):
    dot = path.rindex('.')
    try:
        return getattr(__import__(path[:dot], {}, {}, ['']), path[dot+1:])
    except ImportError:
        if not fail_silently:
            raise

    return None


class PagePretender(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_absolute_url(self):
        return self.url


class NavigationExtension(object):
    __metaclass__ = TypeRegistryMetaClass
    name = _('navigation extension')

    def children(self, page, **kwargs):
        raise NotImplementedError


class PageManager(models.Manager):
    def active(self):
        return self.filter(active=True)

    def page_for_path(self, path, raise404=False):
        """
        Return a page for a path.

        Example:
        Page.objects.page_for_path(request.path)
        """

        stripped = path.strip('/')

        try:
            return self.active().filter(override_url='/%s/' % stripped)[0]
        except IndexError:
            pass

        tokens = stripped.split('/')

        count = len(tokens)

        filters = {'%sisnull' % ('parent__' * count): True}

        for n, token in enumerate(tokens):
            filters['%sslug' % ('parent__' * (count-n-1))] = token

        try:
            return self.active().filter(**filters)[0]
        except IndexError:
            if raise404:
                raise Http404
            raise self.model.DoesNotExist

    def page_for_path_or_404(self, path):
        """
        Wrapper for page_for_path which raises a Http404 if no page
        has been found for the passed path.
        """
        return self.page_for_path(path, raise404=True)

    def best_match_for_path(self, path, raise404=False):
        """
        Return the best match for a path.
        """

        tokens = path.strip('/').split('/')

        for count in range(len(tokens), -1, -1):
            try:
                return self.page_for_path('/'.join(tokens[:count]))
            except self.model.DoesNotExist:
                pass

        if raise404:
            raise Http404
        return None

    def in_navigation(self):
        return self.active().filter(in_navigation=True)

    def toplevel_navigation(self):
        return self.in_navigation().filter(parent__isnull=True)

    def for_request(self, request, raise404=False):
        page = self.page_for_path(request.path, raise404)
        page.setup_request(request)
        return page

    def for_request_or_404(self, request):
        return self.page_for_path_or_404(request.path, raise404=True)

    def best_match_for_request(self, request, raise404=False):
        page = self.best_match_for_path(request.path, raise404)
        page.setup_request(request)
        return page

    def from_request(self, request):
        if hasattr(request, '_feincms_page'):
            return request._feincms_page

        return self.for_request(request)


class Page(Base):
    active = models.BooleanField(_('active'), default=False)

    # structure and navigation
    title = models.CharField(_('title'), max_length=100,
        help_text=_('This is used for the generated navigation too.'))
    slug = models.SlugField()
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    in_navigation = models.BooleanField(_('in navigation'), default=True)
    override_url = models.CharField(_('override URL'), max_length=200, blank=True,
        help_text=_('Override the target URL for the navigation.'))
    redirect_to = models.CharField(_('redirect to'), max_length=200, blank=True,
        help_text=_('Target URL for automatic redirects.'))
    _cached_url = models.CharField(_('Cached URL'), max_length=200, blank=True,
        editable=False, default='')

    # navigation extensions
    NE_CHOICES = [(
        '%s.%s' % (cls.__module__, cls.__name__), cls.name) for cls in NavigationExtension.types]
    navigation_extension = models.CharField(_('navigation extension'),
        choices=NE_CHOICES, blank=True, max_length=50,
        help_text=_('Select the module providing subpages for this page if you need to customize the navigation.'))

    # content
    _content_title = models.TextField(_('content title'), blank=True,
        help_text=_('The first line is the main title, the following lines are subtitles.'))

    # meta stuff TODO keywords and description?
    _page_title = models.CharField(_('page title'), max_length=100, blank=True,
        help_text=_('Page title for browser window. Same as title by default.'))
    meta_keywords = models.TextField(_('meta keywords'), blank=True,
        help_text=_('This will be prepended to the default keyword list.'))
    meta_description = models.TextField(_('meta description'), blank=True,
        help_text=_('This will be prepended to the default description.'))

    # language
    language = models.CharField(_('language'), max_length=10,
        choices=settings.LANGUAGES)
    translations = models.ManyToManyField('self', blank=True)

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    objects = PageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.get_absolute_url())

    def save(self, *args, **kwargs):
        super(Page, self).save(*args, **kwargs)
        pages = self.get_descendants(include_self=True)
        for page in pages:
            page._generate_cached_url()

    def _generate_cached_url(self):
        if self.override_url:
            self._cached_url = self.override_url
        if self.is_root_node():
            self._cached_url = u'/%s/' % (self.slug)
        else:
            self._cached_url = u'/%s/%s/' % ('/'.join([page.slug for page in self.get_ancestors()]), self.slug)

        super(Page, self).save()

    def get_absolute_url(self):
        return self._cached_url

    @property
    def page_title(self):
        if self._page_title:
            return self._page_title
        return self.content_title

    @property
    def content_title(self):
        if not self._content_title:
            return self.title

        try:
            return self._content_title.splitlines()[0]
        except IndexError:
            return u''

    @property
    def content_subtitle(self):
        return u'\n'.join(self._content_title.splitlines()[1:])

    def setup_request(self, request):
        translation.activate(self.language)
        request.LANGUAGE_CODE = translation.get_language()
        request._feincms_page = self

    def extended_navigation(self):
        if not self.navigation_extension:
            return []

        cls = get_object(self.navigation_extension, fail_silently=True)
        if not cls:
            return []

        return cls().children(self)

mptt.register(Page)


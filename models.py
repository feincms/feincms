from django.conf import settings
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

import mptt


class Region(models.Model):
    key = models.CharField(_('key'), max_length=20, unique=True)
    title = models.CharField(_('title'), max_length=50, unique=True)
    inherited = models.BooleanField(_('inherited'), default=False,
        help_text=_('Check this if content of this region should be inherited by subpages.'))

    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')

    def __unicode__(self):
        return self.key


class Template(models.Model):
    title = models.CharField(max_length=200)
    path = models.CharField(max_length=200)
    regions = models.ManyToManyField(Region, related_name='templates')

    class Meta:
        ordering = ['title']
        verbose_name = _('template')
        verbose_name_plural = _('templates')

    def get_blocks(self):
        return self.blocks.split(',')

    def __unicode__(self):
        return self.title


class PageManager(models.Manager):
    def active(self):
        return self.filter(active=True)

    def page_for_path(self, path, raise404=False):
        """
        Return a page for a path.
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

    def from_request(self, request, raise404=False):
        page = self.page_for_path(request.path, raise404)
        page.setup_request(request)
        return page

    def from_request_or_404(self, request):
        return self.page_for_path_or_404(request.path, raise404=True)

    def best_match_from_request(self, request, raise404=False):
        page = self.best_match_for_path(request.path, raise404)
        page.setup_request(request)
        return page


class Page(models.Model):
    active = models.BooleanField(_('active'), default=False)
    template = models.ForeignKey(Template)

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
        ordering = ['lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    objects = PageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.get_absolute_url())

    def get_absolute_url(self):
        if self.override_url:
            return self.override_url
        if self.is_root_node():
            return u'/%s/' % (self.slug)
        else:
            return u'/%s/%s/' % ('/'.join([page.slug for page in self.get_ancestors()]), self.slug)

    @property
    def content(self):
        if not hasattr(self, '_content_proxy'):
            self._content_proxy = ContentProxy(self, self.template)

        return self._content_proxy

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

mptt.register(Page)


class ContentProxy(object):
    """
    This proxy offers attribute-style access to the page contents of regions.

    Example:
    >>> page = Page.objects.all()[0]
    >>> page.content.main
    [A list of all page contents which are assigned to the region with key 'main']
    """

    def __init__(self, page, template):
        self.page = page
        self.template = template

    def __getattr__(self, attr):
        """
        Get all page content instances for the specified page and region

        If no page contents could be found for the current page and the region
        has the inherited flag set, this method will go up the ancestor chain
        until either some page contents have found or no ancestors are left.
        """

        try:
            region = self.__dict__['template'].regions.get(key=attr)
        except Region.DoesNotExist:
            return []

        def collect_items(page):
            contents = []
            for cls in PageContent.types:
                queryset = getattr(page, '%s_set' % cls.__name__.lower())
                contents += list(queryset.filter(region=region))

            if not contents and page.parent_id and region.inherited:
                return collect_items(page.parent)

            return contents

        contents = collect_items(self.__dict__['page'])
        contents.sort(key=lambda c: c.ordering)
        return contents


class PageContentRegistry(models.base.ModelBase):
    """
    You can access the list of PageContent subclasses as PageContent.types
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'types'):
            cls.types = []
        else:
            cls.types.append(cls)


class PageContent(models.Model):
    __metaclass__ = PageContentRegistry

    page = models.ForeignKey(Page, related_name='%(class)s_set')
    region = models.ForeignKey(Region)
    ordering = models.IntegerField(_('ordering'), default=0)

    class Meta:
        abstract = True
        ordering = ['ordering']

    def __unicode__(self):
        return u'%s on %s, ordering %s' % (self.region, self.page, self.ordering)

    def render(self):
        render_fn = getattr(self, 'render_%s' % self.region.key, None)

        if render_fn:
            return render_fn()

        raise NotImplementedError


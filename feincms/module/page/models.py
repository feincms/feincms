from django.contrib import admin
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils.translation import ugettext_lazy as _

import mptt

from feincms.admin import editor
from feincms.models import Region, Template, Base, ContentProxy
from feincms.utils import get_object


class PageManager(models.Manager):

    # A list of filters which are used to determine whether a page is active or not.
    # Extended for example in the datepublisher extension (date-based publishing and
    # un-publishing of pages)
    active_filters = [
        Q(active=True),
        ]

    def active(self):
        queryset = self.all()

        for filt in self.active_filters:
            if callable(filt):
                queryset = filt(queryset)
            else:
                queryset = queryset.filter(filt)

        return queryset

    def page_for_path(self, path, raise404=False):
        """
        Return a page for a path.

        Example:
        Page.objects.page_for_path(request.path)
        """

        stripped = path.strip('/')

        try:
            return self.active().get(_cached_url=stripped and u'/%s/' % stripped or '/')
        except self.model.DoesNotExist:
            if raise404:
                raise Http404
            raise

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
    slug = models.SlugField(_('slug'))
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children')
    in_navigation = models.BooleanField(_('in navigation'), default=True)
    override_url = models.CharField(_('override URL'), max_length=200, blank=True,
        help_text=_('Override the target URL. Be sure to include slashes at the beginning and at the end if it is a local URL. This affects both the navigation and subpages\' URLs.'))
    redirect_to = models.CharField(_('redirect to'), max_length=200, blank=True,
        help_text=_('Target URL for automatic redirects.'))
    _cached_url = models.CharField(_('Cached URL'), max_length=200, blank=True,
        editable=False, default='', db_index=True)

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    objects = PageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self._cached_url)

    def save(self, *args, **kwargs):
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

        # make sure that we get the descendants back after their parents
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

    def get_absolute_url(self):
        return self._cached_url

    def setup_request(self, request):
        request._feincms_page = self

        if 'frontend_editing' in request.GET and request.user.has_module_perms('page'):
            request.session['frontend_editing'] = request.GET['frontend_editing'] and True or False

    @classmethod
    def register_extensions(cls, *extensions):
        for ext in extensions:
            fn = get_object('feincms.module.page.extensions.%s.register' % ext)
            fn(cls, PageAdmin)

mptt.register(Page)


class PageAdmin(editor.ItemEditor, editor.TreeEditor):
    # the fieldsets config here is used for the add_view, it has no effect
    # for the change_view which is completely customized anyway
    fieldsets = (
        (None, {
            'fields': ('active', 'in_navigation', 'template_key', 'title', 'slug',
                'parent'),
        }),
        (_('Other options'), {
            'classes': ('collapse',),
            'fields': ('override_url',),
        }),
        )
    list_display=('title', '_cached_url', 'active', 'in_navigation',
        'template')
    list_filter=('active', 'in_navigation', 'template_key')
    search_fields = ('title', 'slug', '_content_title', '_page_title',
        'meta_keywords', 'meta_description')
    prepopulated_fields={
        'slug': ('title',),
        }

    show_on_top = ('title', 'active')

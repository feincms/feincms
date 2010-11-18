# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------

import sys

from django import forms
from django.core.cache import cache as django_cache
from django.conf import settings as django_settings
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, signals
from django.forms.models import model_to_dict
from django.forms.util import ErrorList
from django.http import Http404, HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _, ugettext
from django.db.transaction import commit_on_success

import mptt

from feincms import settings, ensure_completely_loaded
from feincms.admin import editor
from feincms.admin import item_editor
from feincms.management.checker import check_database_schema
from feincms.models import Base, create_base_model
from feincms.utils import get_object, copy_model_instance
import feincms.admin.filterspecs


# ------------------------------------------------------------------------
class ActiveAwareContentManagerMixin(object):
    """
    Implement what's necessary to add some kind of "active" state for content
    objects. The notion of active is defined by a number of filter rules that
    must all match (AND) for the object to be active.

    A Manager for a content class using the "datepublisher" extension
    should either adopt this mixin or implement a similar interface.
    """

    # A list of filters which are used to determine whether a page is active or not.
    # Extended for example in the datepublisher extension (date-based publishing and
    # un-publishing of pages)
    active_filters = ()

    @classmethod
    def apply_active_filters(cls, queryset):
        """
        Return a queryset reflecting the filters defined.
        """
        for filt in cls.active_filters:
            if callable(filt):
                queryset = filt(queryset)
            else:
                queryset = queryset.filter(filt)

        return queryset

    @classmethod
    def add_to_active_filters(cls, filter):
        """
        Add a new clause to the active filters. A filter may be either
        a Q object to be applied to the content class or a callable taking
        a queryset and spitting out a new one.
        """
        if not cls.active_filters:
            cls.active_filters = list()
        cls.active_filters.append(filter)

    def active(self):
        """
        Return only currently active objects.
        """
        return self.apply_active_filters(self)

# ------------------------------------------------------------------------
def path_to_cache_key(path):
    from django.utils.encoding import iri_to_uri
    path = iri_to_uri(path)
    return 'PAGE-FOR-URL-%d-%s' % ( django_settings.SITE_ID, path )

class PageManager(models.Manager, ActiveAwareContentManagerMixin):

    # The fields which should be excluded when creating a copy. The mptt fields are
    # excluded automatically by other mechanisms
    # ???: Then why are the mptt fields listed here?
    exclude_from_copy = ['id', 'tree_id', 'lft', 'rght', 'level', 'redirect_to']

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
        Return the best match for a path. If the path as given is unavailable,
        continues to search by chopping path components off the end.

        Tries hard to avoid unnecessary database lookups by generating all
        possible matching URL prefixes and choosing the longtest match.

        Page.best_match_for_path('/photos/album/2008/09') might return the
        page with url '/photos/album'.
        """

        paths = ['/']
        path = path.strip('/')

        # Cache path -> page resolving.
        # We flush the cache entry on page saving, so the cache should always
        # be up to date.

        if settings.FEINCMS_USE_CACHE:
            ck = path_to_cache_key(path)
            page = django_cache.get(ck)
            if page:
                return page

        if path:
            tokens = path.split('/')
            paths += ['/%s/' % '/'.join(tokens[:i]) for i in range(1, len(tokens)+1)]

        try:
            page = self.active().filter(_cached_url__in=paths).extra(
                select={'_url_length': 'LENGTH(_cached_url)'}).order_by('-_url_length')[0]
            if settings.FEINCMS_USE_CACHE:
                django_cache.set(ck, page)
            return page
        except IndexError:
            if raise404:
                raise Http404

        raise self.model.DoesNotExist

    def in_navigation(self):
        return self.active().filter(in_navigation=True)

    def toplevel_navigation(self):
        return self.in_navigation().filter(parent__isnull=True)

    def for_request(self, request, raise404=False):
        page = self.page_for_path(request.path, raise404)
        page.setup_request(request)
        return page

    def for_request_or_404(self, request):
        return self.for_request(request, raise404=True)

    def best_match_for_request(self, request, raise404=False):
        page = self.best_match_for_path(request.path, raise404)
        page.setup_request(request)
        return page

    def from_request(self, request):
        if hasattr(request, '_feincms_page'):
            return request._feincms_page

        return self.for_request(request)

    def create_copy(self, page):
        """
        Creates an identical copy of a page except that the new one is
        inactive.
        """

        new = copy_model_instance(page, exclude=self.exclude_from_copy)
        new.active = False
        new.save()
        new.copy_content_from(page)

        return new

    def replace(self, page, with_page):
        page.active = False
        page.save()
        with_page.active = True
        with_page.save()

        for child in page.children.all():
            child.parent = Page.objects.get(pk=with_page.pk)
            child.save()

        # reload to ensure that the mptt attributes in the DB
        # and in our objects are equal
        page = Page.objects.get(pk=page.pk)
        with_page = Page.objects.get(pk=with_page.pk)
        with_page.move_to(page, 'right')

        return Page.objects.get(pk=with_page.pk)

PageManager.add_to_active_filters( Q(active=True) )

# MARK: -
# ------------------------------------------------------------------------

try:
    # MPTT 0.4
    from mptt.models import MPTTModel
    mptt_register = False
    Base = create_base_model(MPTTModel)
except ImportError:
    # MPTT 0.3
    mptt_register = True


class Page(Base):

    active = models.BooleanField(_('active'), default=False)

    # structure and navigation
    title = models.CharField(_('title'), max_length=200,
        help_text=_('This is used for the generated navigation too.'))
    slug = models.SlugField(_('slug'), max_length=150)
    parent = models.ForeignKey('self', verbose_name=_('Parent'), blank=True, null=True, related_name='children')
    parent.parent_filter = True # Custom list_filter - see admin/filterspecs.py
    in_navigation = models.BooleanField(_('in navigation'), default=False)
    override_url = models.CharField(_('override URL'), max_length=300, blank=True,
        help_text=_('Override the target URL. Be sure to include slashes at the beginning and at the end if it is a local URL. This affects both the navigation and subpages\' URLs.'))
    redirect_to = models.CharField(_('redirect to'), max_length=300, blank=True,
        help_text=_('Target URL for automatic redirects.'))
    _cached_url = models.CharField(_('Cached URL'), max_length=300, blank=True,
        editable=False, default='', db_index=True)

    request_processors = []
    response_processors = []
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

    def active_children(self):
        """
        Returns a queryset describing all active children of the current page.
        This is different than page.get_descendants (from mptt) as it will
        additionally select only child pages that are active.
        """
        return Page.objects.active().filter(parent=self)

    def active_children_in_navigation(self):
        """
        Returns a queryset describing all active children that also have the
        in_navigation flag set. This might be used eg. in building navigation
        menues (only show a disclosure indicator if there actually is something
        to disclose).
        """
        return self.active_children().filter(in_navigation=True)

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
        if settings.FEINCMS_USE_CACHE:
            ck = path_to_cache_key( self._original_cached_url.strip('/') )
            django_cache.delete(ck)

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
            super(Page, page).save() # do not recurse

    def get_absolute_url(self):
        return self._cached_url

    def get_preview_url(self):
        try:
            return reverse('feincms_preview', kwargs={ 'page_id': self.id })
        except:
            return None

    def get_navigation_url(self):
        return self.redirect_to or self._cached_url

    def get_siblings_and_self(page):
        return page.get_siblings(include_self=True)

    def cache_key(self):
        """
        Return a string that may be used as cache key for the current page.
        The cache_key is unique for each content type and content instance.
        """
        return '-'.join(unicode(x(self)) for x in self.cache_key_components)

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

    def setup_request(self, request):
        """
        Before rendering a page, run all registered request processors. A request
        processor may peruse and modify the page or the request. It can also return
        a HttpResponse for shortcutting the page rendering and returning that response
        immediately to the client.
        """
        request._feincms_page = self
        request._feincms_extra_context = {}
        request.extra_path = ""

        for fn in self.request_processors:
            r = fn(self, request)
            if r: return r

    def finalize_response(self, request, response):
        """
        After rendering a page to a response, the registered response processors are
        called to modify the response, eg. for setting cache or expiration headers,
        keeping statistics, etc.
        """
        for fn in self.response_processors:
            fn(self, request, response)

    def require_path_active_request_processor(self, request):
        """
        Checks whether any ancestors are actually inaccessible (ie. not
        inactive or expired) and raise a 404 if so.
        """
        if not self.are_ancestors_active():
            raise Http404()

    def get_redirect_to_target(self, request):
        """
        This might be overriden/extended by extension modules.
        """
        return self.redirect_to

    def redirect_request_processor(self, request):
        target = self.get_redirect_to_target(request)
        if target:
            return HttpResponseRedirect(target)

    def frontendediting_request_processor(self, request):
        if not 'frontend_editing' in request.GET:
            return

        if request.user.has_module_perms('page'):
            try:
                enable_fe = int(request.GET['frontend_editing']) > 0
            except ValueError:
                enable_fe = False

            request.session['frontend_editing'] = enable_fe

        # Redirect to cleanup URLs
        return HttpResponseRedirect(request.path)

    def etag_request_processor(self, request):

        # XXX is this a performance concern? Does it create a new class
        # every time the processor is called or is this optimized to a static
        # class??
        class DummyResponse(dict):
            """
            This is a dummy class with enough behaviour of HttpResponse so we
            can use the condition decorator without too much pain.
            """
            def has_header(self, what):
                return False

        def dummy_response_handler(*args, **kwargs):
            return DummyResponse()

        def etagger(request, page, *args, **kwargs):
            etag = page.etag(request)
            return etag

        # Unavailable in Django 1.0 -- the current implementation of ETag support
        # requires Django 1.1 unfortunately.
        from django.views.decorators.http import condition

        # Now wrap the condition decorator around our dummy handler:
        # the net effect is that we will be getting a DummyResponse from
        # the handler if processing is to continue and a non-DummyResponse
        # (should be a "304 not modified") if the etag matches.
        rsp = condition(etag_func=etagger)(dummy_response_handler)(request, self)

        # If dummy then don't do anything, if a real response, return and
        # thus shortcut the request processing.
        if not isinstance(rsp, DummyResponse):
            return rsp

    def etag_response_processor(self, request, response):
        """
        Response processor to set an etag header on outgoing responses.
        The Page.etag() method must return something valid as etag content
        whenever you want an etag header generated.
        """
        etag = self.etag(request)
        if etag is not None:
            response['ETag'] = '"' + etag + '"'

    @staticmethod
    def debug_sql_queries_response_processor(verbose=False, file=sys.stderr):
        if not django_settings.DEBUG:
            return lambda self, request, response: None

        def processor(self, request, response):
            from django.db import connection

            print_sql = lambda x: x
            try:
                import sqlparse
                print_sql = lambda x: sqlparse.format(x, reindent=True, keyword_case='upper')
            except:
                pass

            if verbose:
                print >> file, "--------------------------------------------------------------"
            time = 0.0
            i = 0
            for q in connection.queries:
                i += 1
                if verbose:
                    print >> file, "%d : [%s]\n%s\n" % ( i, q['time'], print_sql(q['sql']))
                time += float(q['time'])

            print >> file, "--------------------------------------------------------------"
            print >> file, "Total: %d queries, %.3f ms" % (i, time)
            print >> file, "--------------------------------------------------------------"

        return processor

    @classmethod
    def register_request_processors(cls, *processors):
        cls.request_processors[0:0] = processors

    @classmethod
    def register_response_processors(cls, *processors):
        cls.response_processors.extend(processors)

    @classmethod
    def register_extension(cls, register_fn):
        register_fn(cls, PageAdmin)


# ------------------------------------------------------------------------
if mptt_register: # MPTT 0.3 legacy support
    mptt.register(Page)

# Our default request processors
Page.register_request_processors(Page.require_path_active_request_processor,
                                 Page.frontendediting_request_processor,
                                 Page.redirect_request_processor)

signals.post_syncdb.connect(check_database_schema(Page, __name__), weak=False)

# MARK: -
# ------------------------------------------------------------------------
class PageAdminForm(forms.ModelForm):
    never_copy_fields = ('title', 'slug', 'parent', 'active', 'override_url',
        'translation_of')

    def __init__(self, *args, **kwargs):
        if 'initial' in kwargs:
            if 'parent' in kwargs['initial']:
                # Prefill a few form values from the parent page
                try:
                    page = Page.objects.get(pk=kwargs['initial']['parent'])
                    data = model_to_dict(page)

                    for field in PageManager.exclude_from_copy:
                        if field in data:
                            del data[field]

                    # These are always excluded from prefilling
                    for field in self.never_copy_fields:
                        if field in data:
                            del data[field]

                    kwargs['initial'].update(data)
                except Page.DoesNotExist:
                    pass

            elif 'translation_of' in kwargs['initial']:
                # Only if translation extension is active
                try:
                    page = Page.objects.get(pk=kwargs['initial']['translation_of'])
                    original = page.original_translation

                    data = {
                        'translation_of': original.id,
                        'template_key': original.template_key,
                        'active': original.active,
                        'in_navigation': original.in_navigation,
                        }

                    if original.parent:
                        try:
                            data['parent'] = original.parent.get_translation(kwargs['initial']['language']).id
                        except Page.DoesNotExist:
                            # ignore this -- the translation does not exist
                            pass

                    kwargs['initial'].update(data)
                except Page.DoesNotExist:
                    pass

        super(PageAdminForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            choices = []
            for key, template in kwargs['instance'].TEMPLATE_CHOICES:
                template = kwargs['instance']._feincms_templates[key]
                if template.preview_image:
                    choices.append((template.key,
                                    mark_safe(u'<img src="%s" alt="%s" /> %s' % (
                                              template.preview_image, template.key, template.title))))
                else:
                    choices.append((template.key, template.title))

            self.fields['template_key'].choices = choices

    def clean(self):
        cleaned_data = super(PageAdminForm, self).clean()

        # No need to think further, let the user correct errors first
        if self._errors:
            return cleaned_data

        current_id = None
        # See the comment below on why we do not use Page.objects.active(),
        # at least for now.
        active_pages = Page.objects.filter(active=True)

        if self.instance:
            current_id = self.instance.id
            active_pages = active_pages.exclude(id=current_id)

        if not cleaned_data['active']:
            # If the current item is inactive, we do not need to conduct
            # further validation. Note that we only check for the flag, not
            # for any other active filters. This is because we do not want
            # to inspect the active filters to determine whether two pages
            # really won't be active at the same time.
            return cleaned_data

        if cleaned_data['override_url']:
            if active_pages.filter(_cached_url=cleaned_data['override_url']).count():
                self._errors['override_url'] = ErrorList([_('This URL is already taken by an active page.')])
                del cleaned_data['override_url']

            return cleaned_data

        if current_id:
            # We are editing an existing page
            parent = Page.objects.get(pk=current_id).parent
        else:
            # The user tries to create a new page
            parent = cleaned_data['parent']

        if parent:
            new_url = '%s%s/' % (parent._cached_url, cleaned_data['slug'])
        else:
            new_url = '/%s/' % cleaned_data['slug']

        if active_pages.filter(_cached_url=new_url).count():
            self._errors['active'] = ErrorList([_('This URL is already taken by another active page.')])
            del cleaned_data['active']

        return cleaned_data


# ------------------------------------------------------------------------


class PageAdmin(editor.ItemEditor, editor.TreeEditor):
    class Media:
        css = {}
        js = []

    form = PageAdminForm

    # the fieldsets config here is used for the add_view, it has no effect
    # for the change_view which is completely customized anyway
    unknown_fields = ['override_url', 'redirect_to']
    fieldsets = [
        (None, {
            'fields': ['active', 'in_navigation', 'template_key', 'title', 'slug',
                'parent'],
        }),
        item_editor.FEINCMS_CONTENT_FIELDSET,
        (_('Other options'), {
            'classes': ['collapse',],
            'fields': unknown_fields,
        }),
        ]
    readonly_fields = []
    list_display = ['short_title', 'is_visible_admin', 'in_navigation_toggle', 'template']
    list_filter = ['active', 'in_navigation', 'template_key', 'parent']
    search_fields = ['title', 'slug']
    prepopulated_fields = { 'slug': ('title',), }

    raw_id_fields = ['parent']
    radio_fields = {'template_key': admin.HORIZONTAL}

    def __init__(self, *args, **kwargs):
        ensure_completely_loaded()

        if len(Page._feincms_templates) > 4:
            del(self.radio_fields['template_key'])

        super(PageAdmin, self).__init__(*args, **kwargs)

        # The use of fieldsets makes only fields explicitly listed in there
        # actually appear in the admin form. However, extensions should not be
        # aware that there is a fieldsets structure and even less modify it;
        # we therefore enumerate all of the model's field and forcibly add them
        # to the last section in the admin. That way, nobody is left behind.
        from django.contrib.admin.util import flatten_fieldsets
        present_fields = flatten_fieldsets(self.fieldsets)

        for f in self.model._meta.fields:
            if not f.name.startswith('_') and not f.name in ('id', 'lft', 'rght', 'tree_id', 'level') and \
                    not f.auto_created and not f.name in present_fields and f.editable:
                self.unknown_fields.append(f.name)
                if not f.editable:
                    self.readonly_fields.append(f.name)

    in_navigation_toggle = editor.ajax_editable_boolean('in_navigation', _('in navigation'))

    def _actions_column(self, page):
        actions = super(PageAdmin, self)._actions_column(page)
        actions.insert(0, u'<a href="add/?parent=%s" title="%s"><img src="%simg/admin/icon_addlink.gif" alt="%s"></a>' % (
            page.pk, _('Add child page'), django_settings.ADMIN_MEDIA_PREFIX ,_('Add child page')))
        actions.insert(0, u'<a href="%s" title="%s"><img src="%simg/admin/selector-search.gif" alt="%s" /></a>' % (
            page.get_absolute_url(), _('View on site'), django_settings.ADMIN_MEDIA_PREFIX, _('View on site')))
        return actions

    def add_view(self, request, form_url='', extra_context=None):
        # Preserve GET parameters
        return super(PageAdmin, self).add_view(
            request=request,
            form_url=request.get_full_path(),
            extra_context=extra_context)

    def response_add(self, request, obj, *args, **kwargs):
        response = super(PageAdmin, self).response_add(request, obj, *args, **kwargs)
        if 'parent' in request.GET and '_addanother' in request.POST and response.status_code in (301, 302):
            # Preserve GET parameters if we are about to add another page
            response['Location'] += '?parent=%s' % request.GET['parent']
        if 'translation_of' in request.GET:
            # Copy all contents
            try:
                original = self.model._tree_manager.get(pk=request.GET.get('translation_of'))
                original = original.original_translation
                obj.copy_content_from(original)
                obj.save()
            except self.model.DoesNotExist:
                pass

        return response

    def _refresh_changelist_caches(self, *args, **kwargs):
        self._visible_pages = list(self.model.objects.active().values_list('id', flat=True))

    def change_view(self, request, object_id, extra_context=None):
        from django.shortcuts import get_object_or_404
        if 'create_copy' in request.GET:
            page = get_object_or_404(Page, pk=object_id)
            new = Page.objects.create_copy(page)
            self.message_user(request, ugettext("You may edit the copied page below."))
            return HttpResponseRedirect('../%s/' % new.pk)
        elif 'replace' in request.GET:
            page = get_object_or_404(Page, pk=request.GET.get('replace'))
            with_page = get_object_or_404(Page, pk=object_id)
            Page.objects.replace(page, with_page)
            self.message_user(request, ugettext("You have replaced %s. You may continue editing the now-active page below.") % page)
            return HttpResponseRedirect('.')

        # Hack around a Django bug: raw_id_fields aren't validated correctly for
        # ForeignKeys in 1.1: http://code.djangoproject.com/ticket/8746 details
        # the problem - it was fixed for MultipleChoiceFields but not ModelChoiceField
        # See http://code.djangoproject.com/ticket/9209

        if hasattr(self, "raw_id_fields"):
            for k in self.raw_id_fields:
                if not k in request.POST:
                    continue
                if not isinstance(getattr(Page, k).field, models.ForeignKey):
                    continue

                v = request.POST[k]

                if not v:
                    del request.POST[k]
                    continue

                try:
                    request.POST[k] = int(v)
                except ValueError:
                    request.POST[k] = None

        return super(PageAdmin, self).change_view(request, object_id, extra_context)

    def render_item_editor(self, request, object, context):
        if object:
            try:
                active = Page.objects.active().exclude(pk=object.pk).get(_cached_url=object._cached_url)
                context['to_replace'] = active
            except Page.DoesNotExist:
                pass

        return super(PageAdmin, self).render_item_editor(request, object, context)

    def is_visible_admin(self, page):
        """
        Instead of just showing an on/off boolean, also indicate whether this
        page is not visible because of publishing dates or inherited status.
        """
        if not hasattr(self, "_visible_pages"):
            self._visible_pages = list() # Sanity check in case this is not already defined

        if page.parent_id and not page.parent_id in self._visible_pages:
            # parent page's invisibility is inherited
            if page.id in self._visible_pages:
                self._visible_pages.remove(page.id)
            return editor.ajax_editable_boolean_cell(page, 'active', override=False, text=_('inherited'))

        if page.active and not page.id in self._visible_pages:
            # is active but should not be shown, so visibility limited by extension: show a "not active"
            return editor.ajax_editable_boolean_cell(page, 'active', override=False, text=_('extensions'))

        return editor.ajax_editable_boolean_cell(page, 'active')
    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('is active')
    is_visible_admin.editable_boolean_field = 'active'

    # active toggle needs more sophisticated result function
    def is_visible_recursive(self, page):
        retval = []
        for c in page.get_descendants(include_self=True):
            retval.append(self.is_visible_admin(c))
        return retval
    is_visible_admin.editable_boolean_result = is_visible_recursive

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

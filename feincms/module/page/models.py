# ------------------------------------------------------------------------
# coding=utf-8
# $Id$
# ------------------------------------------------------------------------

from django import forms
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, signals
from django.db.models.signals import post_save
from django.forms.models import model_to_dict
from django.forms.util import ErrorList
from django.http import Http404, HttpResponseRedirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import condition

import mptt

from feincms import settings
from feincms.admin import editor
from feincms.admin.editor import django_boolean_icon
from feincms.management.checker import check_database_schema
from feincms.models import Region, Template, Base, ContentProxy
from feincms.utils import get_object


class PageManager(models.Manager):

    # A list of filters which are used to determine whether a page is active or not.
    # Extended for example in the datepublisher extension (date-based publishing and
    # un-publishing of pages)
    active_filters = [
        Q(active=True),
        ]

    # The fields which should be excluded when creating a copy. The mptt fields are
    # excluded automatically by other mechanisms
    exclude_from_copy = ['id']

    @classmethod
    def apply_active_filters(cls, queryset):
        for filt in cls.active_filters:
            if callable(filt):
                queryset = filt(queryset)
            else:
                queryset = queryset.filter(filt)

        return queryset

    def active(self):
        return self.apply_active_filters(self)

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

        data = model_to_dict(page)
        print data

        for field in self.exclude_from_copy:
            del data[field]
        data['active'] = False
        new = Page.objects.create(**data)
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


# ------------------------------------------------------------------------
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

    request_processors = []
    response_processors = []

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('page')
        verbose_name_plural = _('pages')

    objects = PageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.title, self._cached_url)

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
        Do a short version of the title, truncate it intelligently when too long.
        Try to cut it in 2/3 + ellipsis + 1/3 of the original title. The first part
        also tries to cut at white space instead of in mid-word.
        """
        max_length = 50
        if len(self.title) >= max_length:
            first_part = int(max_length * 0.6)
            next_space = self.title[first_part:(max_length / 2 - first_part)].find(' ')
            if next_space >= 0:
                first_part += next_space
            return self.title[:first_part] + u' … ' + self.title[-(max_length - first_part):]
        return self.title
    short_title.admin_order_field = 'title'
    short_title.short_description = _('title')

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

    def get_preview_url(self):
        try:
            return reverse('feincms_preview', kwargs={ 'page_id': self.id })
        except:
            return None

    def get_navigation_url(self):
        return self.redirect_to or self._cached_url

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

    def redirect_request_processor(self, request):
        if self.redirect_to:
            return HttpResponseRedirect(self.redirect_to)

    def frontendediting_request_processor(self, request):
        if 'frontend_editing' in request.GET and request.user.has_module_perms('page'):
            request.session['frontend_editing'] = request.GET['frontend_editing'] and True or False

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
            response['ETag'] = etag

    @classmethod
    def register_request_processors(cls, *processors):
        cls.request_processors[0:0] = processors

    @classmethod
    def register_response_processors(cls, *processors):
        cls.response_processors.extend(processors)

    @classmethod
    def register_extensions(cls, *extensions):
        if not hasattr(cls, '_feincms_extensions'):
            cls._feincms_extensions = set()

        for ext in extensions:
            if ext in cls._feincms_extensions:
                continue

            fn = get_object('feincms.module.page.extensions.%s.register' % ext)
            fn(cls, PageAdmin)
            cls._feincms_extensions.add(ext)

# ------------------------------------------------------------------------
mptt.register(Page)

# Our default request processors
Page.register_request_processors(Page.require_path_active_request_processor,
                                 Page.frontendediting_request_processor,
                                 Page.redirect_request_processor)

signals.post_syncdb.connect(check_database_schema(Page, __name__), weak=False)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
class PageAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PageAdminForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            choices = []
            for key, template in kwargs['instance']._feincms_templates.items():
                if template.preview_image:
                    choices.append((template.key,
                                    mark_safe(u'<img src="%s" alt="%s" /> %s' % (
                                              template.preview_image, template.key, template.title))))
                else:
                    choices.append((template.key, template.title))

            self.fields['template_key'].choices = choices

    def clean(self):
        cleaned_data = self.cleaned_data

        current_id = None
        # See the comment below on why we do not use Page.objects.active(),
        # at least for now.
        active_pages = Page.objects.filter(active=True)

        if 'id' in self.initial:
            current_id = self.initial['id']
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
class Null(object):
    pass

if settings._FEINCMS_ALTERNATIVE_PAGE_ADMIN:
    list_modeladmin = Null
else:
    if settings.FEINCMS_PAGE_USE_SPLIT_PANE_EDITOR:
        list_modeladmin = editor.SplitPaneEditor
    else:
        list_modeladmin = editor.TreeEditor

# ------------------------------------------------------------------------
def ajax_editable_boolean_cell(item, attr, text='', override=None):
    if text:
        text = '&nbsp;(%s)' % unicode(text)

    if override is not None:
        a = [ django_boolean_icon(override, text), text ]
    else:
        value = getattr(item, attr)
        a = [ 
              '<input type="checkbox" id="%s_%d"' % (attr, item.id),
              value and ' checked="checked"' or '',
              ' onclick="return toggle_boolean(this, \'%s\')";' % attr,
              ' />',
              text,
            ]
    
    a.insert(0, '<div id="wrap_%s_%d">' % ( attr, item.id ))
    a.append('</div>')
    #print a
    return unicode(''.join(a))

#django_boolean_icon(False), _('inherited'))
#    return '<a class="attr_%s" href="#" onclick="return toggle_boolean(this, \'%s\')">%s</a>' % (
#        attr, attr, django_boolean_icon(getattr(item, attr), 'toggle %s' % attr))

# ------------------------------------------------------------------------
def ajax_editable_boolean(attr, short_description):
    """
    Convenience function: Assign the return value of this method to a variable
    of your ModelAdmin class and put the variable name into list_display.

    Example:
        class MyTreeEditor(TreeEditor):
            list_display = ('__unicode__', 'active_toggle')

            active_toggle = ajax_editable_boolean('active', _('is active'))
    """
    def _fn(self, item):
        return ajax_editable_boolean_cell(item, attr)
    _fn.allow_tags = True
    _fn.short_description = short_description
    _fn.editable_boolean_field = attr
    return _fn

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
class PageAdmin(editor.ItemEditor, list_modeladmin):

    class Media:
        css = { 'all' : (settings.FEINCMS_ADMIN_MEDIA + 'ui/jqueryui-custom-1.7.2.css', ) }

        js = []
        if settings.FEINCMS_ADMIN_MEDIA_HOTLINKING:
            js.extend((
                "http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js",
#                "http://ajax.googleapis.com/ajax/libs/jqueryui/1.7.2/jquery-ui.min.js"
                ))
        else:
            js.extend((
                settings.FEINCMS_ADMIN_MEDIA + "jquery-1.3.2.min.js",
#                settings.FEINCMS_ADMIN_MEDIA + "ui/jqueryui-custom-1.7.2.min.js"
                ))
                
        js.extend((
            settings.FEINCMS_ADMIN_MEDIA + "jquery.json-1.3.js",
            ))


    form = PageAdminForm

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
    list_display = ['short_title', 'is_visible_admin', 'in_navigation_toggle', 'template']
    # Use nicer title display showing hierarchy
    if settings._FEINCMS_ALTERNATIVE_PAGE_ADMIN:
        list_display[0] = 'short_title_admin'

    list_filter = ('active', 'in_navigation', 'template_key')
    search_fields = ('title', 'slug', 'meta_keywords', 'meta_description')
    prepopulated_fields = { 'slug': ('title',), }

    raw_id_fields = []

    show_on_top = ('title', 'active')

    radio_fields = {'template_key': admin.HORIZONTAL}

    #

    def short_title_admin(self, page):
        """
        Generate a short title for a page, indent it depending on
        the page's depth in the hierarchy.
        """
        prefix = u''
        if page.level > 0:
            prefix = u' ↳ '
        if page.level > 1:
            prefix = u'   ' * (page.level-1) + prefix
        return prefix + page.short_title()
    short_title_admin.short_description = _('title')

    
    def is_visible_admin(self, page):
        """
        Instead of just showing an on/off boolean, also indicate whether this
        page is not visible because of publishing dates or inherited status.
        """
        if not page.active:
            return ajax_editable_boolean_cell(page, 'active', _('not active'))
            
        if page.parent_id and not page.parent_id in self._visible_pages:
            # parent page's invisibility is inherited
            if page.id in self._visible_pages:
                self._visible_pages.remove(page.id)
                return ajax_editable_boolean_cell(page, 'active', override=False, text=_('inherited'))
            # Fallthru: page is not in self._visible_pages, no need to repeat ourselves
            # return u'%s (%s)' % (django_boolean_icon(False), _('not active by date'))

        if not page.id in self._visible_pages:
            return ajax_editable_boolean_cell(page, 'active', override=False, text=_('by date'))

        return ajax_editable_boolean_cell(page, 'active')
    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('is visible')
    is_visible_admin.editable_boolean_field = 'active'

    # active toggle needs more sophisticated result function
    def is_visible_recursive(self, page):
        retval = []
        for c in page.get_descendants(include_self=True):
            retval.append(self.is_visible_admin(c))

        return map(lambda page: self.is_visible_admin(page), page.get_descendants(include_self=True))

    boolean_toggles = { 'active' : is_visible_recursive }

    
    in_navigation_toggle = ajax_editable_boolean('in_navigation', _('in navigation'))


    def cached_url_admin(self, page):
        return u'<a href="%s">%s</a>' % (page._cached_url, page._cached_url)
    cached_url_admin.allow_tags = True
    cached_url_admin.admin_order_field = '_cached_url'
    cached_url_admin.short_description = _('Cached URL')

    #
    def _collect_editable_booleans(self):
        """
        Collect all fields marked as editable booleans. We do not
        want the user to be able to edit arbitrary fields by crafting
        an AJAX request by hand.
        """
        if hasattr(self, '_ajax_editable_booleans'):
            return

        self._ajax_editable_booleans = []

        for field in self.list_display:
            # The ajax_editable_boolean return value has to be assigned
            # to the ModelAdmin class
            item = getattr(self.__class__, field, None)
            if not item:
                continue

            attr = getattr(item, 'editable_boolean_field', None)
            if attr:
                self._ajax_editable_booleans.append(attr)

    def _toggle_boolean(self, request):
        """
        Handle an AJAX toggle_boolean request
        """
        self._collect_editable_booleans()

        item_id = request.POST.get('item_id')
        attr = request.POST.get('attr')

        if attr not in self._ajax_editable_booleans:
            return HttpResponseBadRequest("not a valid attribute %s" % attr)

        try:
            obj = self.model._default_manager.get(pk=unquote(item_id))
            setattr(obj, attr, not getattr(obj, attr))
            obj.save()
            self.refresh_visible_pages()    # ???: Perhaps better a post_save signal?
        except Exception, e:
            return HttpResponse("FAILED " + unicode(e), mimetype="text/plain")

        # ???: Is there some more elegant solution for this?
        if self.boolean_toggles.has_key(attr):
            data = self.boolean_toggles[attr](self, obj)
        else:
            data = [ ajax_editable_boolean_cell(obj, attr) ]

        return HttpResponse(simplejson.dumps(data), mimetype="application/json")

    def refresh_visible_pages(self, *args, **kwargs):
        self._visible_pages = list(Page.objects.active().values_list('id', flat=True))

    def changelist_view(self, request, extra_context=None, *args, **kwargs):
        """
        Handle the changelist view, the django view for the model instances
        change list/actions page.
        """
        # get a list of all visible pages for use by is_visible_admin
        self.refresh_visible_pages()

        # handle common AJAX requests
        if request.is_ajax():
            cmd = request.POST.get('__cmd')
            if cmd == 'toggle_boolean':
                return self._toggle_boolean(request)

        return super(PageAdmin, self).changelist_view(request, extra_context, *args, **kwargs)



# ------------------------------------------------------------------------
# !!!: Hack alert! Patching ChangeList, check whether this still applies post Django 1.1

# By default, django only orders by first ordering field in admin. We patch
# up the ChangeList here so it returns "use default ordering" for any Page
# lookups. That way, we can order by tree_id + lft and get the site's natural
# page structure.

if settings._FEINCMS_ALTERNATIVE_PAGE_ADMIN:
    from django.contrib.admin.views.main import ChangeList

    __cl_get_ordering = ChangeList.get_ordering
    def __get_ordering(cl):
        if cl.model == Page:
            return '', ''
        return __cl_get_ordering(cl)

    ChangeList.get_ordering = __get_ordering

# ------------------------------------------------------------------------

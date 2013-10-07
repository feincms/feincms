"""
Third-party application inclusion support.
"""

from email.utils import parsedate
from time import mktime
import re

from django.core import urlresolvers
from django.core.urlresolvers import Resolver404, resolve, reverse, NoReverseMatch
from django.db import models
from django.db.models import signals
from django.http import HttpResponse
from django.utils.functional import curry as partial, lazy, wraps
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin.item_editor import ItemEditorForm
from feincms.contrib.fields import JSONField
from feincms.utils import get_object

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

# Used to store MPTT informations about the currently requested
# page. The information will be used to find the best application
# content instance if a particular application has been added
# more than once to the current website.
# Additionally, we store the page class too, because when we have
# more than one page class, reverse() will want to prefer the page
# class used to render the current page. (See issue #240)
_local = local()


def retrieve_page_information(page, request=None):
    """This is the request processor responsible for retrieving information
    about the currently processed page so that we can make an optimal match
    when reversing app URLs when the same ApplicationContent has been added
    several times to the website."""
    _local.proximity_info = (page.tree_id, page.lft, page.rght, page.level)
    _local.page_class = page.__class__
    _local.page_cache_key_fn = page.cache_key


def _empty_reverse_cache(*args, **kwargs):
    _local.reverse_cache = {}


def app_reverse(viewname, urlconf, args=None, kwargs=None, prefix=None,
        *vargs, **vkwargs):
    """
    Reverse URLs from application contents

    Works almost like Django's own reverse() method except that it resolves
    URLs from application contents. The second argument, ``urlconf``, has to
    correspond to the URLconf parameter passed in the ``APPLICATIONS`` list
    to ``Page.create_content_type``::

        app_reverse('mymodel-detail', 'myapp.urls', args=...)

        or

        app_reverse('mymodel-detail', 'myapp.urls', kwargs=...)

    The second argument may also be a request object if you want to reverse
    an URL belonging to the current application content.
    """

    # First parameter might be a request instead of an urlconf path, so
    # we'll try to be helpful and extract the current urlconf from it
    extra_context = getattr(urlconf, '_feincms_extra_context', {})
    appconfig = extra_context.get('app_config', {})
    urlconf = appconfig.get('urlconf_path', urlconf)

    # vargs and vkwargs are used to send through additional parameters which
    # are uninteresting to us (such as current_app)

    # get additional cache keys from the page if available
    # refs https://github.com/feincms/feincms/pull/277/
    fn = getattr(_local, 'page_cache_key_fn', lambda: '')
    cache_key_prefix = fn()

    app_cache_keys = {
        'none': '%s:app_%s_none' % (cache_key_prefix, urlconf),
        }
    proximity_info = getattr(_local, 'proximity_info', None)
    url_prefix = None

    if proximity_info:
        app_cache_keys.update({
            'all': '%s:app_%s_%s_%s_%s_%s' % (
                (cache_key_prefix, urlconf,) + proximity_info),
            'tree': '%s:app_%s_%s' % (
                cache_key_prefix, urlconf, proximity_info[0]),
            })

    for key in ('all', 'tree', 'none'):
        try:
            url_prefix = _local.reverse_cache[app_cache_keys[key]]
            break
        except (AttributeError, KeyError):
            pass
    else:
        try:
            # Take the ApplicationContent class used by the current request
            model_class = _local.page_class.content_type_for(ApplicationContent)
        except AttributeError:
            model_class = None

        if not model_class:
            # Take any
            model_class = ApplicationContent._feincms_content_models[0]

        # TODO: Only active pages? What about multisite support?
        contents = model_class.objects.filter(
            urlconf_path=urlconf).select_related('parent')

        if proximity_info:
            # find the closest match within the same subtree
            tree_contents = contents.filter(parent__tree_id=proximity_info[0])
            if not len(tree_contents):
                # no application contents within the same tree
                cache_key = 'tree'
                try:
                    content = contents[0]
                except IndexError:
                    content = None
            elif len(tree_contents) == 1:
                cache_key = 'tree'
                # just one match within the tree, use it
                content = tree_contents[0]
            else: # len(tree_contents) > 1
                cache_key = 'all'
                try:
                    # select all ancestors and descendants and get the one with
                    # the smallest difference in levels
                    content = (tree_contents.filter(
                        parent__rght__gt=proximity_info[2],
                        parent__lft__lt=proximity_info[1]
                    ) | tree_contents.filter(
                        parent__lft__lte=proximity_info[2],
                        parent__lft__gte=proximity_info[1],
                    )).extra({
                        'level_diff': "abs(100 + level - %d)" % proximity_info[3]
                    }).order_by('level_diff')[0]
                except IndexError:
                    content = tree_contents[0]
        else:
            cache_key = 'none'
            try:
                content = contents[0]
            except IndexError:
                content = None

        if content:
            if urlconf in model_class.ALL_APPS_CONFIG:
                # We have an overridden URLconf
                urlconf = model_class.ALL_APPS_CONFIG[urlconf]['config'].get(
                    'urls', urlconf)

            if not hasattr(_local, 'reverse_cache'):
                _local.reverse_cache = {}

            prefix = content.parent.get_absolute_url()
            prefix += '/' if prefix[-1] != '/' else ''

            _local.reverse_cache[app_cache_keys[cache_key]] = url_prefix = (
                urlconf, prefix)

    if url_prefix:
        return reverse(viewname,
            url_prefix[0],
            args=args,
            kwargs=kwargs,
            prefix=url_prefix[1],
            *vargs, **vkwargs)
    raise NoReverseMatch("Unable to find ApplicationContent for %r" % urlconf)


#: Lazy version of ``app_reverse``
app_reverse_lazy = lazy(app_reverse, str)


def permalink(func):
    """
    Decorator that calls app_reverse()

    Use this instead of standard django.db.models.permalink if you want to
    integrate the model through ApplicationContent. The wrapped function
    must return 4 instead of 3 arguments::

        class MyModel(models.Model):
            @appmodels.permalink
            def get_absolute_url(self):
                return ('myapp.urls', 'model_detail', (), {'slug': self.slug})
    """
    def inner(*args, **kwargs):
        return app_reverse(*func(*args, **kwargs))
    return wraps(func)(inner)


APPLICATIONCONTENT_RE = re.compile(r'^([^/]+)/([^/]+)$')


class ApplicationContent(models.Model):
    #: parameters is used to serialize instance-specific data which will be
    # provided to the view code. This allows customization (e.g. "Embed
    # MyBlogApp for blog <slug>")
    parameters = JSONField(null=True, editable=False)

    ALL_APPS_CONFIG = {}

    class Meta:
        abstract = True
        verbose_name = _('application content')
        verbose_name_plural = _('application contents')

    @classmethod
    def initialize_type(cls, APPLICATIONS):
        for i in APPLICATIONS:
            if not 2 <= len(i) <= 3:
                raise ValueError(
                    "APPLICATIONS must be provided with tuples containing at"
                    " least two parameters (urls, name) and an optional extra"
                    " config dict")

            urls, name = i[0:2]

            if len(i) == 3:
                app_conf = i[2]

                if not isinstance(app_conf, dict):
                    raise ValueError(
                        "The third parameter of an APPLICATIONS entry must be"
                        " a dict or the name of one!")
            else:
                app_conf = {}

            cls.ALL_APPS_CONFIG[urls] = {
                "urls":     urls,
                "name":     name,
                "config":   app_conf
            }

        cls.add_to_class('urlconf_path',
            models.CharField(_('application'), max_length=100, choices=[
                (c['urls'], c['name']) for c in cls.ALL_APPS_CONFIG.values()])
        )

        class ApplicationContentItemEditorForm(ItemEditorForm):
            app_config    = {}
            custom_fields = {}

            def __init__(self, *args, **kwargs):
                super(ApplicationContentItemEditorForm, self).__init__(*args, **kwargs)

                instance = kwargs.get("instance", None)

                if instance:
                    try:
                        # TODO use urlconf_path from POST if set
                        # urlconf_path = request.POST.get('...urlconf_path',
                        #     instance.urlconf_path)
                        self.app_config = cls.ALL_APPS_CONFIG[
                            instance.urlconf_path]['config']
                    except KeyError:
                        self.app_config = {}

                    self.custom_fields = {}
                    admin_fields = self.app_config.get('admin_fields', {})

                    if isinstance(admin_fields, dict):
                        self.custom_fields.update(admin_fields)
                    else:
                        get_fields = get_object(admin_fields)
                        self.custom_fields.update(
                            get_fields(self, *args, **kwargs))

                    for k, v in self.custom_fields.items():
                        self.fields[k] = v

            def save(self, commit=True, *args, **kwargs):
                # Django ModelForms return the model instance from save. We'll
                # call save with commit=False first to do any necessary work &
                # get the model so we can set .parameters to the values of our
                # custom fields before calling save(commit=True)

                m = super(ApplicationContentItemEditorForm, self).save(
                    commit=False, *args, **kwargs)

                m.parameters = dict((k, self.cleaned_data[k]) for k
                    in self.custom_fields if k in self.cleaned_data)

                if commit:
                    m.save(**kwargs)

                return m

        # This provides hooks for us to customize the admin interface for
        # embedded instances:
        cls.feincms_item_editor_form = ApplicationContentItemEditorForm

        # Make sure the patched reverse() method has all information it needs
        cls.parent.field.rel.to.register_request_processor(
            retrieve_page_information)

        signals.post_save.connect(_empty_reverse_cache, sender=cls)
        signals.post_delete.connect(_empty_reverse_cache, sender=cls)

    def __init__(self, *args, **kwargs):
        super(ApplicationContent, self).__init__(*args, **kwargs)
        self.app_config = self.ALL_APPS_CONFIG.get(
            self.urlconf_path, {}).get('config', {})

    def process(self, request, **kw):
        page_url = self.parent.get_absolute_url()

        # Provide a way for appcontent items to customize URL processing by
        # altering the perceived path of the page:
        if "path_mapper" in self.app_config:
            path_mapper = get_object(self.app_config["path_mapper"])
            path, page_url = path_mapper(
                request.path,
                page_url,
                appcontent_parameters=self.parameters
            )
        else:
            path = request._feincms_extra_context['extra_path']

        # Resolve the module holding the application urls.
        urlconf_path = self.app_config.get('urls', self.urlconf_path)

        try:
            fn, args, kwargs = resolve(path, urlconf_path)
        except (ValueError, Resolver404):
            raise Resolver404('Not found (resolving %r in %r failed)' % (
                path, urlconf_path))

        # Variables from the ApplicationContent parameters are added to request
        # so we can expose them to our templates via the appcontent_parameters
        # context_processor
        request._feincms_extra_context.update(self.parameters)

        # Save the application configuration for reuse elsewhere
        request._feincms_extra_context.update({
            'app_config': dict(self.app_config,
                urlconf_path=self.urlconf_path)})

        view_wrapper = self.app_config.get("view_wrapper", None)
        if view_wrapper:
            fn = partial(
                get_object(view_wrapper),
                view=fn,
                appcontent_parameters=self.parameters
            )

        output = fn(request, *args, **kwargs)

        if isinstance(output, HttpResponse):
            if self.send_directly(request, output):
                return output
            elif output.status_code == 200:

                # If the response supports deferred rendering, render the
                # response right now. We do not handle template response
                # middleware.
                if hasattr(output, 'render') and callable(output.render):
                    output.render()

                self.rendered_result = mark_safe(
                    output.content.decode('utf-8'))
                self.rendered_headers = {}

                # Copy relevant headers for later perusal
                for h in ('Cache-Control', 'Last-Modified', 'Expires'):
                    if h in output:
                        self.rendered_headers.setdefault(
                            h, []).append(output[h])

        elif isinstance(output, tuple) and 'view' in kw:
            kw['view'].template_name = output[0]
            kw['view'].request._feincms_extra_context.update(output[1])
        else:
            self.rendered_result = mark_safe(output)

        return True # successful

    def send_directly(self, request, response):
        mimetype = response.get('Content-Type', 'text/plain')
        if ';' in mimetype:
            mimetype = mimetype.split(';')[0]
        mimetype = mimetype.strip()

        return (response.status_code != 200
                or request.is_ajax()
                or getattr(response, 'standalone', False)
                or mimetype not in ('text/html', 'text/plain'))

    def render(self, **kwargs):
        return getattr(self, 'rendered_result', u'')

    def finalize(self, request, response):
        headers = getattr(self, 'rendered_headers', None)
        if headers:
            self._update_response_headers(request, response, headers)

    def _update_response_headers(self, request, response, headers):
        """
        Combine all headers that were set by the different content types
        We are interested in Cache-Control, Last-Modified, Expires
        """
        from django.utils.http import http_date

        # Ideally, for the Cache-Control header, we'd want to do some
        # intelligent combining, but that's hard. Let's just collect and unique
        # them and let the client worry about that.
        cc_headers = set(('must-revalidate',))
        for x in (cc.split(",") for cc in headers.get('Cache-Control', ())):
            cc_headers |= set((s.strip() for s in x))

        if len(cc_headers):
            response['Cache-Control'] = ", ".join(cc_headers)
        else:   # Default value
            response['Cache-Control'] = 'no-cache, must-revalidate'

        # Check all Last-Modified headers, choose the latest one
        lm_list = [parsedate(x) for x in headers.get('Last-Modified', ())]
        if len(lm_list) > 0:
            response['Last-Modified'] = http_date(mktime(max(lm_list)))

        # Check all Expires headers, choose the earliest one
        lm_list = [parsedate(x) for x in headers.get('Expires', ())]
        if len(lm_list) > 0:
            response['Expires'] = http_date(mktime(min(lm_list)))

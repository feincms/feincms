"""
Third-party application inclusion support.
"""

from time import mktime
import re

from django.core import urlresolvers
from django.core.urlresolvers import Resolver404, resolve, reverse as _reverse, NoReverseMatch
from django.db import models
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

try:
    from functools import partial
except ImportError:
    from django.utils.functional import curry as partial

from feincms.admin.editor import ItemEditorForm
from feincms.contrib.fields import JSONField
from feincms.utils import get_object

try:
    from email.utils import parsedate
except ImportError: # py 2.4 compat
    from email.Utils import parsedate

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_local = local()


def retrieve_page_information(page, request=None):
    _local.proximity_info = (page.tree_id, page.lft, page.rght, page.level)


def _empty_reverse_cache():
    _local.reverse_cache = {}


APPLICATIONCONTENT_RE = re.compile(r'^([^/]+)/([^/]+)$')


def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, *vargs, **vkwargs):
    """
    This reverse replacement adds two new capabilities to the Django reverse method:

    - If reverse is called from inside ``ApplicationContent.process``, it
      automatically prepends the URL of the page the ``ApplicationContent``
      is attached to, thereby allowing ``reverse`` and ``{% url %}`` to
      return correct URLs without hard-coding the application integration
      point into the templates or URLconf files.
    - If the viewname contains a slash, the part before the slash is
      interpreted as the path to an URLconf file. This allows the template
      author to resolve URLs only reachable via an ``ApplicationContent``,
      even inside another application contents' ``process`` method::

          {% url registration.urls/auth_logout %}
    """

    if isinstance(viewname, basestring) and APPLICATIONCONTENT_RE.match(viewname):
        # try to reverse an URL inside another applicationcontent
        other_urlconf, other_viewname = viewname.split('/')

        # TODO do not use internal feincms data structures as much
        model_class = ApplicationContent._feincms_content_models[0]

        if hasattr(_local, 'urlconf') and other_urlconf == _local.urlconf[0]:
            # We are reversing an URL from our own ApplicationContent
            return _reverse(other_viewname, other_urlconf, args, kwargs, _local.urlconf[1], *vargs, **vkwargs)

        if not hasattr(_local, 'reverse_cache'):
            _local.reverse_cache = {}


        # try different cache keys of descending specificity, this one always works
        urlconf_cache_keys = {
            'none': '%s_noprox' % other_urlconf,
        }

        # when we have more proximity info, we can use more specific cache keys
        proximity_info = getattr(_local, 'proximity_info', None)
        if proximity_info:
            urlconf_cache_keys.update({
                'all': '%s_%s_%s_%s_%s' % ((other_urlconf,) + proximity_info),
                'tree': '%s_%s' % (other_urlconf, proximity_info[0]),
            })

        for key in ('all', 'tree', 'none'):
            if key in urlconf_cache_keys and urlconf_cache_keys[key] in _local.reverse_cache:
                content = _local.reverse_cache[urlconf_cache_keys[key]]
                break
        else:
            contents = model_class.objects.filter(
                urlconf_path=other_urlconf).select_related('parent')

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
                        )).extra({'level_diff':"abs(level-%d)" % proximity_info[3]}
                            ).order_by('level_diff')[0]
                    except IndexError:
                        content = tree_contents[0]
            else:
                cache_key = 'none'
                try:
                    content = contents[0]
                except IndexError:
                    content = None
            _local.reverse_cache[urlconf_cache_keys[cache_key]] = content

        if content:
            # Save information from _urlconfs in case we are inside another
            # application contents' ``process`` method currently
            saved_cfg = getattr(_local, 'urlconf', None)

            if other_urlconf in model_class.ALL_APPS_CONFIG:
                # We have an overridden URLconf
                other_urlconf = model_class.ALL_APPS_CONFIG[other_urlconf]['config'].get(
                    'urls', other_urlconf)

            # Initialize application content reverse hackery for the other application
            _local.urlconf = (other_urlconf, content.parent.get_absolute_url())

            try:
                url = reverse(other_viewname, other_urlconf, args, kwargs, prefix, *vargs, **vkwargs)
            except:
                url = None

            if saved_cfg:
                _local.urlconf = saved_cfg
            else:
                del _local.urlconf

            # We found an URL somewhere in here... return it. Otherwise, we continue
            # below
            if url:
                return url

    if hasattr(_local, 'urlconf'):
        # Special handling inside ApplicationContent.render; override urlconf
        # and prefix variables so that reverse works as expected.
        urlconf1, prefix1 = _local.urlconf
        try:
            return _reverse(viewname, urlconf1, args, kwargs, prefix1, *vargs, **vkwargs)
        except NoReverseMatch:
            # fall through to calling reverse with default arguments
            pass

    return _reverse(viewname, urlconf, args, kwargs, prefix, *vargs, **vkwargs)
urlresolvers.reverse = reverse


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
        # Generate a more flexible application configuration structure from
        # the legacy pattern:

        # TODO: Consider changing the input signature to something cleaner, at
        # the cost of a one-time backwards incompatible change

        for i in APPLICATIONS:
            if not 2 <= len(i) <= 3:
                raise ValueError("APPLICATIONS must be provided with tuples containing at least two parameters (urls, name) and an optional extra config dict")

            urls, name = i[0:2]

            if len(i) == 3:
                app_conf = i[2]

                if not isinstance(app_conf, dict):
                    raise ValueError("The third parameter of an APPLICATIONS entry must be a dict or the name of one!")
            else:
                app_conf = {}

            cls.ALL_APPS_CONFIG[urls] = {
                "urls":     urls,
                "name":     name,
                "config":   app_conf
            }

        cls.add_to_class('urlconf_path',
            models.CharField(_('application'), max_length=100, choices=[(c['urls'], c['name']) for c in cls.ALL_APPS_CONFIG.values()])
        )

        class ApplicationContentItemEditorForm(ItemEditorForm):
            app_config    = {}
            custom_fields = {}

            def __init__(self, *args, **kwargs):
                super(ApplicationContentItemEditorForm, self).__init__(*args, **kwargs)

                instance = kwargs.get("instance", None)

                if instance:
                    try:
                        self.app_config = cls.ALL_APPS_CONFIG[instance.urlconf_path]['config']
                    except KeyError:
                        self.app_config = {}

                    self.custom_fields = {}
                    admin_fields    = self.app_config.get('admin_fields', {})

                    if isinstance(admin_fields, dict):
                        self.custom_fields.update(admin_fields)
                    else:
                        get_fields = get_object(admin_fields)
                        self.custom_fields.update(get_fields(self, *args, **kwargs))

                    for k, v in self.custom_fields.items():
                        self.fields[k] = v


            def clean(self, *args, **kwargs):
                cleaned_data = super(ApplicationContentItemEditorForm, self).clean(*args, **kwargs)

                # TODO: Check for newly added instances so we can force a re-validation of their custom fields

                return cleaned_data

            def save(self, commit=True, *args, **kwargs):
                # Django ModelForms return the model instance from save. We'll
                # call save with commit=False first to do any necessary work &
                # get the model so we can set .parameters to the values of our
                # custom fields before calling save(commit=True)

                m = super(ApplicationContentItemEditorForm, self).save(commit=False, *args, **kwargs)

                m.parameters = dict((k, self.cleaned_data[k]) for k in self.custom_fields if k in self.cleaned_data)

                if commit:
                    m.save(**kwargs)

                return m

        #: This provides hooks for us to customize the admin interface for embedded instances:
        cls.feincms_item_editor_form = ApplicationContentItemEditorForm

        # Make sure the patched reverse() method has all information it needs
        cls.parent.field.rel.to.register_request_processors(retrieve_page_information)

    def __init__(self, *args, **kwargs):
        super(ApplicationContent, self).__init__(*args, **kwargs)
        self.app_config = self.ALL_APPS_CONFIG.get(self.urlconf_path, {}).get('config', {})

    def process(self, request, **kw):
        page_url = self.parent.get_absolute_url()

        # Get the rest of the URL

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

        # Change the prefix and urlconf for the monkey-patched reverse function ...
        _local.urlconf = (urlconf_path, page_url)

        try:
            fn, args, kwargs = resolve(path, urlconf_path)
        except (ValueError, Resolver404):
            del _local.urlconf
            raise Resolver404

        #: Variables from the ApplicationContent parameters are added to request
        #  so we can expose them to our templates via the appcontent_parameters
        #  context_processor
        request._feincms_extra_context.update(self.parameters)

        view_wrapper = self.app_config.get("view_wrapper", None)
        if view_wrapper:
            fn = partial(
                get_object(view_wrapper),
                view=fn,
                appcontent_parameters=self.parameters
            )

        try:
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

                    self.rendered_result = mark_safe(output.content.decode('utf-8'))
                    self.rendered_headers = {}
                    # Copy relevant headers for later perusal
                    for h in ('Cache-Control', 'Last-Modified', 'Expires'):
                        if h in output:
                            self.rendered_headers.setdefault(h, []).append(output[h])
            elif isinstance(output, tuple) and 'view' in kw:
                kw['view'].template_name = output[0]
                kw['view'].request._feincms_extra_context.update(output[1])
            else:
                self.rendered_result = mark_safe(output)

        finally:
            # We want exceptions to propagate, but we cannot allow the
            # modifications to reverse() to stay here.
            del _local.urlconf

        return True # successful

    def send_directly(self, request, response):
        return response.status_code != 200 or request.is_ajax() or getattr(response, 'standalone', False)

    def render(self, **kwargs):
        return getattr(self, 'rendered_result', u'')

    def finalize(self, request, response):
        headers = getattr(self, 'rendered_headers', None)
        if headers:
            self._update_response_headers(request, response, headers)

    def save(self, *args, **kwargs):
        super(ApplicationContent, self).save(*args, **kwargs)
        # Clear reverse() cache
        _empty_reverse_cache()

    def delete(self, *args, **kwargs):
        super(ApplicationContent, self).delete(*args, **kwargs)
        # Clear reverse() cache
        _empty_reverse_cache()

    def _update_response_headers(self, request, response, headers):
        """
        Combine all headers that were set by the different content types
        We are interested in Cache-Control, Last-Modified, Expires
        """
        from django.utils.http import http_date

        # Ideally, for the Cache-Control header, we'd want to do some intelligent
        # combining, but that's hard. Let's just collect and unique them and let
        # the client worry about that.
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

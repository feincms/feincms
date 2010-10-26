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

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_local = local()


def retrieve_page_information(page):
    _local.proximity_info = (page.tree_id, page.lft, page.rght, page.level)


def _empty_reverse_cache():
    _local.reverse_cache = {}


APPLICATIONCONTENT_RE = re.compile(r'^([\.\w]+)/([\.\w]+)$')


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

        if hasattr(_local, 'urlconf') and other_urlconf == _local.urlconf[0]:
            # We are reversing an URL from our own ApplicationContent
            return _reverse(other_viewname, other_urlconf, args, kwargs, _local.urlconf[1], *vargs, **vkwargs)

        if not hasattr(_local, 'reverse_cache'):
            _local.reverse_cache = {}

        # Update this when more items are used for the proximity analysis below
        proximity_info = getattr(_local, 'proximity_info', None)
        if proximity_info:
            urlconf_cache_key = '%s_%s' % (other_urlconf, proximity_info[0])
        else:
            urlconf_cache_key = '%s_noprox' % other_urlconf

        if urlconf_cache_key not in _local.reverse_cache:
            # TODO do not use internal feincms data structures as much
            model_class = ApplicationContent._feincms_content_models[0]
            contents = model_class.objects.filter(
                urlconf_path=other_urlconf).select_related('parent')

            if proximity_info:
                # Poor man's proximity analysis. Filter by tree_id :-)
                try:
                    content = contents.get(parent__tree_id=proximity_info[0])
                except (model_class.DoesNotExist, model_class.MultipleObjectsReturned):
                    try:
                        content = contents[0]
                    except IndexError:
                        content = None
            else:
                try:
                    content = contents[0]
                except IndexError:
                    content = None
            _local.reverse_cache[urlconf_cache_key] = content
        else:
            content = _local.reverse_cache[urlconf_cache_key]

        if content:
            # Save information from _urlconfs in case we are inside another
            # application contents' ``process`` method currently
            saved_cfg = getattr(_local, 'urlconf', None)

            # Initialize application content reverse hackery for the other application
            _local.urlconf = (other_urlconf, content.parent.get_absolute_url())

            try:
                url = reverse(other_viewname, other_urlconf, args, kwargs, prefix, *vargs, **vkwargs)
            except:
                # We really must not fail here. We absolutely need to remove/restore
                # the _urlconfs information
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
                    self.app_config = cls.ALL_APPS_CONFIG[instance.urlconf_path]['config']
                    self.custom_fields = {}
                    admin_fields    = self.app_config.get('admin_fields', {})

                    if isinstance(admin_fields, dict):
                        self.custom_fields.update(admin_fields)
                    else:
                        get_fields = urlresolvers.get_callable(admin_fields)
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

    def __init__(self, *args, **kwargs):
        super(ApplicationContent, self).__init__(*args, **kwargs)
        self.app_config = self.ALL_APPS_CONFIG.get(self.urlconf_path, {}).get('config', {})

    def render(self, request, **kwargs):
        return getattr(request, "_feincms_applicationcontents", {}).get(self.id, u'')

    def process(self, request):
        page_url = self.parent.get_absolute_url()

        # Get the rest of the URL

        # Provide a way for appcontent items to customize URL processing by
        # altering the perceived path of the page:
        if "path_mapper" in self.app_config:
            path_mapper = urlresolvers.get_callable(self.app_config["path_mapper"])
            path, page_url = path_mapper(
                request.path,
                page_url,
                appcontent_parameters=self.parameters
            )
        else:
            path = re.sub('^' + re.escape(page_url[:-1]), '', request.path)

        # Change the prefix and urlconf for the monkey-patched reverse function ...
        _local.urlconf = (self.urlconf_path, page_url)

        try:
            fn, args, kwargs = resolve(path, self.urlconf_path)
        except (ValueError, Resolver404):
            del _local.urlconf
            raise Resolver404

        #: Variables from the ApplicationContent parameters are added to request
        #  so we can expose them to our templates via the appcontent_parameters
        #  context_processor
        request._feincms_appcontent_parameters.update(self.parameters)

        view_wrapper = self.app_config.get("view_wrapper", None)
        if view_wrapper:
            fn = partial(
                urlresolvers.get_callable(view_wrapper),
                view=fn,
                appcontent_parameters=self.parameters
            )

        try:
            output = fn(request, *args, **kwargs)
        except:
            # We want exceptions to propagate, but we cannot allow the
            # modifications to reverse() to stay here.
            del _local.urlconf
            raise

        # ... and restore it after processing the view
        del _local.urlconf

        if isinstance(output, HttpResponse):
            if output.status_code == 200:
                if not getattr(output, 'standalone', False):
                    request._feincms_applicationcontents[self.id] = mark_safe(output.content.decode('utf-8'))

            return output
        else:
            request._feincms_applicationcontents[self.id] = mark_safe(output)

    def save(self, *args, **kwargs):
        super(ApplicationContent, self).save(*args, **kwargs)
        # Clear reverse() cache
        _empty_reverse_cache()

    def delete(self, *args, **kwargs):
        super(ApplicationContent, self).delete(*args, **kwargs)
        # Clear reverse() cache
        _empty_reverse_cache()

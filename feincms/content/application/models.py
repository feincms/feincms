import re

from django.core import urlresolvers
from django.core.urlresolvers import Resolver404, resolve, reverse as _reverse, NoReverseMatch
from django.db import models
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.utils.thread_support import currentThread
from django.utils.translation import ugettext_lazy as _


_urlconfs = {}

OTHER_APPLICATIONCONTENT_SEPARATOR = '/'

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

    ct = currentThread()

    if OTHER_APPLICATIONCONTENT_SEPARATOR in viewname:
        # try to reverse an URL inside another applicationcontent
        other_urlconf, other_viewname = viewname.split(OTHER_APPLICATIONCONTENT_SEPARATOR)

        # TODO do not use internal feincms data structures as much
        contents = ApplicationContent._feincms_content_models[0].objects.filter(urlconf_path=other_urlconf)

        # TODO find best matching ac (using language, nearness in tree etc)
        content = contents[0] # :-)

        # Save information from _urlconfs in case we are inside another
        # application contents' ``process`` method currently
        saved_cfg = None
        if ct in _urlconfs:
            saved_cfg = _urlconfs[ct]

        # Initialize application content reverse hackery for the other application
        _urlconfs[ct] = (other_urlconf, content.parent.get_absolute_url())

        try:
            url = reverse(other_viewname, other_urlconf, args, kwargs, prefix, *vargs, **vkwargs)
        except:
            # We really must not fail here. We absolutely need to remove/restore
            # the _urlconfs information
            url = None

        if saved_cfg:
            _urlconfs[ct] = saved_cfg
        else:
            del _urlconfs[ct]

        # We found an URL somewhere in here... return it. Otherwise, we continue
        # below
        if url:
            return url

    if ct in _urlconfs:
        # Special handling inside ApplicationContent.render; override urlconf
        # and prefix variables so that reverse works as expected.
        urlconf1, prefix1 = _urlconfs[ct]
        try:
            return _reverse(viewname, urlconf1, args, kwargs, prefix1, *vargs, **vkwargs)
        except NoReverseMatch:
            # fall through to calling reverse with default arguments
            pass

    return _reverse(viewname, urlconf, args, kwargs, prefix, *vargs, **vkwargs)
urlresolvers.reverse = reverse


class ApplicationContent(models.Model):
    class Meta:
        abstract = True
        verbose_name = _('application content')
        verbose_name_plural = _('application contents')

    @classmethod
    def initialize_type(cls, APPLICATIONS):
        cls.add_to_class('urlconf_path', models.CharField(_('application'), max_length=100,
                                                          choices=APPLICATIONS))

    def render(self, request, **kwargs):
        return request._feincms_applicationcontents.get(self.id, u'')

    def process(self, request):
        # prepare storage for rendered application contents
        if not hasattr(request, '_feincms_applicationcontents'):
            request._feincms_applicationcontents = {}
            request._feincms_applicationcontents_fragments = {}

        page_url = self.parent.get_absolute_url()

        # Get the rest of the URL
        path = re.sub('^' + re.escape(page_url[:-1]), '', request.path)

        # Change the prefix and urlconf for the monkey-patched reverse function ...
        _urlconfs[currentThread()] = (self.urlconf_path, page_url)

        try:
            fn, args, kwargs = resolve(path, self.urlconf_path)
        except (ValueError, Resolver404):
            # Silent failure if resolving failed
            del _urlconfs[currentThread()]
            return

        try:
            output = fn(request, *args, **kwargs)
        except:
            # We want exceptions to propagate, but we cannot allow the
            # modifications to reverse() to stay here.
            del _urlconfs[currentThread()]
            raise

        # ... and restore it after processing the view
        del _urlconfs[currentThread()]

        if isinstance(output, HttpResponse):
            if output.status_code == 200:
                request._feincms_applicationcontents[self.id] = mark_safe(output.content.decode('utf-8'))

            return output
        else:
            request._feincms_applicationcontents[self.id] = mark_safe(output)

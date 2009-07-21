import re

from django.conf import settings
from django.core import urlresolvers
from django.core.urlresolvers import Resolver404, resolve, reverse as _reverse, NoReverseMatch
from django.db import models
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.utils.thread_support import currentThread
from django.utils.translation import ugettext_lazy as _


_urlconfs = {}

def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, *vargs, **vkwargs):
    ct = currentThread()
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
    urlconf_path = models.CharField(_('URLconf path'), max_length=100)

    class Meta:
        abstract = True
        verbose_name = _('application content')
        verbose_name_plural = _('application contents')

    def render(self, request, **kwargs):
        return request._feincms_applicationcontents.get(self.id, u'')

    def process(self, request):
        # prepare storage for rendered application contents
        if not hasattr(request, '_feincms_applicationcontents'):
            request._feincms_applicationcontents = {}

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
                request._feincms_applicationcontents[self.id] = mark_safe(output.content)

            # return response if view returned a HttpResponse, but not a 200
            return output
        else:
            request._feincms_applicationcontents[self.id] = mark_safe(output)

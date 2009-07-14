import datetime

from django.db import models
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page

class ViewContent(models.Model):

    '''
    at the moment, these are not used
    but in further deployment they will be filled up by a command which automatically generate the tree
    '''
    viewname = models.CharField(max_length=255, editable=False, blank=True)
    viewfunc = models.CharField(max_length=255, editable=False, blank=True)

    class Meta:
        abstract = True
        verbose_name = _("view content")

    def render(self, **kwargs):
        request = kwargs.get('request')
        try:
            return unicode(request._feincms_page.vc_manager[self.id])
        except AttributeError:
            return _("Could not parse the view content because the view is excluded from infanta handling.")
        except KeyError:
            if self.viewname and self.viewfunc:
                return _("Placeholder for the %(viewname)s calling %(viewfunc)s" % {'viewname': self.viewname, 'viewfunc': self.viewfunc})
            if self.viewfunc:
                return _("Placeholder for calling %(viewfunc)s" % {'viewfunc': self.viewfunc})
            return 'no content registered for this view content'

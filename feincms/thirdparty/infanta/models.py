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
        verbose_name = _("View Content")
    
    def render(self, **kwargs):
        request = kwargs.get('request')
        try:
            return str(request._feincms_page.vc_manager[self.id])
        except KeyError:
            if self.viewname and self.viewfunc:
                return _("Placeholder for the %s calling %s" % (self.viewname, self.viewfunc))
            if self.viewfunc:
                return _("Placeholder for calling %s" % (self.viewfunc))
            return 'no content registered for this view content'
    



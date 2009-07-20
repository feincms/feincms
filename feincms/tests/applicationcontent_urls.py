"""
This is a dummy module used to test the ApplicationContent
"""

from django.conf.urls.defaults import *
from django.http import HttpResponse


def module_root(request):
    return 'module_root'


def args_test(request, kwarg1, kwarg2):
    return HttpResponse(u'%s-%s' % (kwarg1, kwarg2))


urlpatterns = patterns('',
    url(r'^$', module_root),
    url(r'^args_test/([^/]+)/([^/]+)/$', args_test),
    url(r'^kwargs_test/(?P<kwarg2>[^/]+)/(?P<kwarg1>[^/]+)/$', args_test),
)

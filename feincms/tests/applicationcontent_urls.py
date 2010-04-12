"""
This is a dummy module used to test the ApplicationContent
"""

from django import template
from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseRedirect


def module_root(request):
    return 'module_root'


def args_test(request, kwarg1, kwarg2):
    return HttpResponse(u'%s-%s' % (kwarg1, kwarg2))


def reverse_test(request):
    t = template.Template('home:{% url ac_module_root %} args:{% url ac_args_test "xy" "zzy" %} base:{% url feincms.views.applicationcontent.handler "test" %}')
    return t.render(template.Context())


def raises(request):
    raise NotImplementedError, 'not really not implemented, but it is as good as anything for the test'


def fragment(request):
    t = template.Template('{% load applicationcontent_tags %}{% fragment request "something" %}some things{% endfragment %}')
    return t.render(template.Context({'request': request}))


def redirect(request):
    return HttpResponseRedirect('../')


urlpatterns = patterns('',
    url(r'^$', module_root, name='ac_module_root'),
    url(r'^args_test/([^/]+)/([^/]+)/$', args_test, name='ac_args_test'),
    url(r'^kwargs_test/(?P<kwarg2>[^/]+)/(?P<kwarg1>[^/]+)/$', args_test),
    url(r'^reverse_test/$', reverse_test),
    url(r'^raises/$', raises),
    url(r'^fragment/$', fragment),
    url(r'^redirect/$', redirect),
)

"""
This is a dummy module used to test the ApplicationContent
"""

from django import template
from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseRedirect

from feincms.views.decorators import standalone


def module_root(request):
    return 'module_root'


def args_test(request, kwarg1, kwarg2):
    return HttpResponse(u'%s-%s' % (kwarg1, kwarg2))


def reverse_test(request):
    t = template.Template('home:{% url ac_module_root %} args:{% url ac_args_test "xy" "zzy" %} base:{% url feincms_handler "test" %}')
    return t.render(template.Context())


def full_reverse_test(request):
    t = template.Template('home:{% url feincms.tests.applicationcontent_urls/ac_module_root %} args:{% url feincms.tests.applicationcontent_urls/ac_args_test "xy" "zzy" %} base:{% url feincms_handler "test" %}')
    return t.render(template.Context())


def alias_reverse_test(request):
    t = template.Template('home:{% url whatever/ac_module_root %} args:{% url whatever/ac_args_test "xy" "zzy" %} base:{% url feincms_handler "test" %}')
    return t.render(template.Context())


def fragment(request):
    t = template.Template('{% load applicationcontent_tags %}{% fragment request "something" %}some things{% endfragment %}')
    return t.render(template.Context({'request': request}))


def redirect(request):
    return HttpResponseRedirect('../')


def response(request):
    return HttpResponse('Anything')


def inheritance20(request):
    return template.Template('''
            {% extends "base.html" %}
            some content outside
            {% block content %}a content {{ from_appcontent }}{% endblock %}
            {% block sidebar %}b content {{ block.super }}{% block bla %}{% endblock %}{% endblock %}
            '''), {'from_appcontent': 42}


urlpatterns = patterns('',
    url(r'^$', module_root, name='ac_module_root'),
    url(r'^args_test/([^/]+)/([^/]+)/$', args_test, name='ac_args_test'),
    url(r'^kwargs_test/(?P<kwarg2>[^/]+)/(?P<kwarg1>[^/]+)/$', args_test),
    url(r'^reverse_test/$', reverse_test),
    url(r'^full_reverse_test/$', full_reverse_test),
    url(r'^alias_reverse_test/$', alias_reverse_test),
    url(r'^fragment/$', fragment),
    url(r'^redirect/$', redirect),
    url(r'^response/$', response),
    url(r'^response_decorated/$', standalone(response)),
    url(r'^inheritance20/$', inheritance20),
)

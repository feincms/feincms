"""
This is a dummy module used to test the ApplicationContent
"""

from __future__ import absolute_import, unicode_literals

from django.conf.urls import patterns, url
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string

from feincms.views.decorators import standalone


def module_root(request):
    return 'module_root'


def args_test(request, kwarg1, kwarg2):
    return HttpResponse('%s-%s' % (kwarg1, kwarg2))


def full_reverse_test(request):
    return render_to_string('full_reverse_test.html', {})


def alias_reverse_test(request):
    return render_to_string('alias_reverse_test.html', {})


def fragment(request):
    return render_to_string('fragment.html', {'request': request})


def redirect(request):
    return HttpResponseRedirect('../')


def response(request):
    return HttpResponse('Anything')


def inheritance20(request):
    return 'inheritance20.html', {'from_appcontent': 42}


urlpatterns = patterns(
    '',
    url(r'^$', module_root, name='ac_module_root'),
    url(r'^args_test/([^/]+)/([^/]+)/$', args_test, name='ac_args_test'),
    url(r'^kwargs_test/(?P<kwarg2>[^/]+)/(?P<kwarg1>[^/]+)/$', args_test),
    url(r'^full_reverse_test/$', full_reverse_test),
    url(r'^alias_reverse_test/$', alias_reverse_test),
    url(r'^fragment/$', fragment),
    url(r'^redirect/$', redirect),
    url(r'^response/$', response),
    url(r'^response_decorated/$', standalone(response)),
    url(r'^inheritance20/$', inheritance20),
)

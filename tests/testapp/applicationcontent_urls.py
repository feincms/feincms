"""
This is a dummy module used to test the ApplicationContent
"""

from __future__ import absolute_import, unicode_literals

from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from feincms.content.application.models import standalone, unpack


try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path


def module_root(request):
    return HttpResponse("module_root")


def args_test(request, kwarg1, kwarg2):
    return HttpResponse("%s-%s" % (kwarg1, kwarg2))


def full_reverse_test(request):
    return render_to_string("full_reverse_test.html", {})


def alias_reverse_test(request):
    return render_to_string("alias_reverse_test.html", {})


def fragment(request):
    return render_to_string("fragment.html", {"request": request})


def redirect(request):
    return HttpResponseRedirect(request.build_absolute_uri("../"))


def response(request):
    return HttpResponse("Anything")


def inheritance20(request):
    return "inheritance20.html", {"from_appcontent": 42}


@unpack
def inheritance20_unpack(request):
    response = TemplateResponse(request, "inheritance20.html", {"from_appcontent": 43})
    response["Cache-Control"] = "yabba dabba"
    return response


urlpatterns = [
    re_path(r"^$", module_root, name="ac_module_root"),
    re_path(r"^args_test/([^/]+)/([^/]+)/$", args_test, name="ac_args_test"),
    re_path(r"^kwargs_test/(?P<kwarg2>[^/]+)/(?P<kwarg1>[^/]+)/$", args_test),
    re_path(r"^full_reverse_test/$", full_reverse_test),
    re_path(r"^alias_reverse_test/$", alias_reverse_test),
    re_path(r"^fragment/$", fragment),
    re_path(r"^redirect/$", redirect),
    re_path(r"^response/$", response),
    re_path(r"^response_decorated/$", standalone(response)),
    re_path(r"^inheritance20/$", inheritance20),
    re_path(r"^inheritance20_unpack/$", inheritance20_unpack),
]

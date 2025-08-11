"""
This is a dummy module used to test the ApplicationContent
"""

from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import path, re_path

from feincms.content.application.models import standalone, unpack


def module_root(request):
    return HttpResponse("module_root")


def args_test(request, kwarg1, kwarg2):
    return HttpResponse(f"{kwarg1}-{kwarg2}")


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
    path("", module_root, name="ac_module_root"),
    re_path(r"^args_test/([^/]+)/([^/]+)/$", args_test, name="ac_args_test"),
    path("kwargs_test/<str:kwarg2>/<str:kwarg1>/", args_test),
    path("full_reverse_test/", full_reverse_test),
    path("alias_reverse_test/", alias_reverse_test),
    path("fragment/", fragment),
    path("redirect/", redirect),
    path("response/", response),
    path("response_decorated/", standalone(response)),
    path("inheritance20/", inheritance20),
    path("inheritance20_unpack/", inheritance20_unpack),
]

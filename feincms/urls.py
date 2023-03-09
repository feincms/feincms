from django.urls import path, re_path

from feincms.views import Handler


handler = Handler.as_view()

urlpatterns = [
    path("", handler, name="feincms_home"),
    re_path(r"^(.*)/$", handler, name="feincms_handler"),
]

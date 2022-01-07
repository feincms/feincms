from django.urls import re_path

from feincms.views import Handler


handler = Handler.as_view()

urlpatterns = [
    re_path(r"^$", handler, name="feincms_home"),
    re_path(r"^(.*)/$", handler, name="feincms_handler"),
]

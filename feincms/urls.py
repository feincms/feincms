# flake8: noqa
from __future__ import absolute_import

from feincms.views import Handler


try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path


handler = Handler.as_view()

urlpatterns = [
    re_path(r"^$", handler, name="feincms_home"),
    re_path(r"^(.*)/$", handler, name="feincms_handler"),
]

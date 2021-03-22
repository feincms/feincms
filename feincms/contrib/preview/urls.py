try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path

from feincms.contrib.preview.views import PreviewHandler


urlpatterns = [
    re_path(r"^(.*)/_preview/(\d+)/$", PreviewHandler.as_view(), name="feincms_preview")
]

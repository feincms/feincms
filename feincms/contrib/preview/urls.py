from django.urls import re_path

from feincms.contrib.preview.views import PreviewHandler


urlpatterns = [
    re_path(r"^(.*)/_preview/(\d+)/$", PreviewHandler.as_view(), name="feincms_preview")
]

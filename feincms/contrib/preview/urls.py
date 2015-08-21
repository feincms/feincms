from django.conf.urls import url

from feincms.contrib.preview.views import PreviewHandler


urlpatterns = [
    url(r'^(.*)/_preview/(\d+)/$', PreviewHandler.as_view(),
        name='feincms_preview'),
]

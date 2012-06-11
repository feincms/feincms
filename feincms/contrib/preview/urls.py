from django.conf.urls import patterns, include, url

from feincms.contrib.preview.views import PreviewHandler

urlpatterns = patterns('',
    url(r'^(.*)/_preview/(\d+)/$', PreviewHandler.as_view(), name='feincms_preview'),
)

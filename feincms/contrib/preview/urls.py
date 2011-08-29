from django.conf.urls.defaults import *

from feincms.contrib.preview.views import PreviewHandler

urlpatterns = patterns('',
    url(r'^(.*)/_preview/(\d+)/$', PreviewHandler.as_view(), name='feincms_preview'),
)

from django.conf.urls.defaults import *

from feincms.views import base

urlpatterns = patterns('',
    url(r'^(?:.*)/_preview/(?P<page_id>\d+)/', base.preview_handler, name='feincms_preview'),
    url(r'^$', base.handler, name='feincms_home'),
    url(r'^(.*)/$', base.handler, name='feincms_handler'),
)

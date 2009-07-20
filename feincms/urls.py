from django.conf.urls.defaults import *

from feincms.views import base

urlpatterns = patterns('',
    url(r'^preview/(?P<page_id>\d+)/', base.preview_handler, name='feincms:preview'),
    url(r'^$|^(.*)/$', base.handler), # catch empty URLs (root page) or URLs ending with a slash
)

from django.conf.urls.defaults import *

from feincms.views import ajax, base

urlpatterns = patterns('',
    url(r'^admin-ajax/toggle/', ajax.toggle, name='feincms:ajax:toggle'),
    url(r'^preview/(?P<page_id>\d+)/', base.preview_handler, name='feincms:preview'),
    url(r'^(.*)$', base.handler),
)
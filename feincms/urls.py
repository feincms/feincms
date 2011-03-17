from django.conf.urls.defaults import *

from feincms.views import base

urlpatterns = patterns('',
    url(r'^$', base.handler, name='feincms_home'),
    url(r'^(.*)/$', base.handler, name='feincms_handler'),
)


from __future__ import absolute_import

from django.conf.urls.defaults import patterns, url

from .views import Handler
handler = Handler.as_view()

urlpatterns = patterns('',
    url(r'^$', handler, name='feincms_home'),
    url(r'^(.*)/$', handler, name='feincms_handler'),
)

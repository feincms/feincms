from django.conf.urls.defaults import *

from feincms.views.cbv import Handler
handler = Handler.as_view()

urlpatterns = patterns('',
    url(r'^$', handler, name='feincms_home'),
    url(r'^(.*)/$', handler, name='feincms_handler'),
)

from django.conf.urls.defaults import patterns, include, url

from feincms.views.cbv.views import Handler
handler = Handler.as_view()

urlpatterns = patterns('',
    url(r'^$', handler, name='feincms_home'),
    url(r'^(.*)/$', handler, name='feincms_handler'),
)

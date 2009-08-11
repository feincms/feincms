from django.conf.urls.defaults import *

from feincms.views import base
# from feincms.views import applicationcontent

urlpatterns = patterns('',
    url(r'^preview/(?P<page_id>\d+)/', base.preview_handler, name='feincms_preview'),
    # url(r'^$|^(.*)/$', applicationcontent.handler),
    url(r'^$|^(.*)/$', base.handler), # catch empty URLs (root page) or URLs ending with a slash
)

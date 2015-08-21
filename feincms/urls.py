# flake8: noqa
from __future__ import absolute_import

from django.conf.urls import url

from feincms.views import Handler

handler = Handler.as_view()

urlpatterns = [
    url(r'^$', handler, name='feincms_home'),
    url(r'^(.*)/$', handler, name='feincms_handler'),
]

import os

from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^example/', include('example.foo.urls')),

    # This avoids breaking Django admin's localization JavaScript when using
    # the FeinCMS frontend editing:
    url(r'admin/page/page/jsi18n/',     'django.views.generic.simple.redirect_to', {'url': '/admin/jsi18n/'}),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    #(r'^admin/', include(admin.site.urls)),
    (r'^admin/', include(admin.site.urls) ),

    (r'^feincms_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'feincms/static/feincms/')}),

    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': os.path.join(os.path.dirname(__file__), 'media/')}),

    (r'^', include('feincms.views.cbv.urls')),
)

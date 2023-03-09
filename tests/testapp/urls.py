import os

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views.static import serve

from feincms.module.page.sitemap import PageSitemap


sitemaps = {"pages": PageSitemap}

admin.autodiscover()

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": os.path.join(os.path.dirname(__file__), "media/")},
    ),
    re_path(r"^sitemap\.xml$", sitemap, {"sitemaps": sitemaps}),
    path("", include("feincms.contrib.preview.urls")),
    path("", include("feincms.urls")),
]

urlpatterns += staticfiles_urlpatterns()

from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms.module.page.models import PageManager


def current_site(queryset):
    return queryset.filter(site=Site.objects.get_current())


class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class(
            'site',
            models.ForeignKey(
                Site, verbose_name=_('Site'), default=settings.SITE_ID))

        PageManager.add_to_active_filters(current_site, key='current_site')

    def handle_modeladmin(self, modeladmin):
        modeladmin.extend_list('list_display', ['site'])
        modeladmin.extend_list('list_filter', ['site'])
        modeladmin.add_extension_options('site')

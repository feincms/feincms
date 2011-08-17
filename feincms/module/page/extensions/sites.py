from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site

from feincms.module.page.models import PageManager


def current_site(queryset):
    return queryset.filter(site=Site.objects.get_current())


def register(cls, admin_cls):
    cls.add_to_class('site',
                     models.ForeignKey(Site,
                     verbose_name=_('Site'),
                     default=settings.SITE_ID, ))

    PageManager.add_to_active_filters(current_site, key='current_site')

    admin_cls.list_display.extend(['site'])

from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db import models
from django.contrib.sites.models import Site

from feincms.module.page.models import PageManager


def register(cls, admin_cls):
    "Add a foreign key on Site to the Page model"
    cls.add_to_class('site',
                     models.ForeignKey(Site,
                     verbose_name=_('Site'),
                     default=settings.SITE_ID, ))

    # If the site does not match, the page is not active
    PageManager.add_to_active_filters(models.Q(site=settings.SITE_ID))

    # Show the site on the admin list
    admin_cls.list_display.extend(['site'])

    # Filter Pages by site
    admin_cls.list_filter.extend(['site'])

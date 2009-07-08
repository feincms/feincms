"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the default
views and the template tags.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page, PageAdmin

def is_visible(self):
    now = datetime.now()

    return self.active and \
           self.publication_date <= now and \
           (self.publication_end_date is None or self.publication_end_date > now)
is_visible.boolean = True

def register():
    Page.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=datetime.now))
    Page.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True))

    Page.objects.active_filters.append(
            Q(publication_date__lte=datetime.now) and \
            (Q(publication_end_date__isnull=True) or Q(publication_end_date__gt=datetime.now)))
    
    Page.visible = is_visible

    PageAdmin.list_display.insert(2, 'visible')
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from feincms.module.page.models import Page, PageAdmin


def register():
    Page.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=datetime.now))
    Page.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True))

    Page.objects.active_filters.append(
            Q(publication_date__lte=datetime.now)
            & (Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=datetime.now)))

"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the default
views and the template tags.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


def register(cls, admin_cls):
    cls.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=datetime.now))
    cls.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True))

    cls.objects.active_filters.append(
            Q(publication_date__lte=datetime.now)
            & (Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=datetime.now)))

    def datepublisher_admin(self, page):
        if page.publication_end_date:
            return u'%s &ndash; %s' % (
                page.publication_date.strftime('%d.%m.%Y'),
                page.publication_end_date.strftime('%d.%m.%Y'),
                )

        return u'%s &ndash; &infin;' % (
            page.publication_date.strftime('%d.%m.%Y'),
            )

    datepublisher_admin.allow_tags = True
    datepublisher_admin.short_description = _('date publisher')
    admin_cls.datepublisher_admin = datepublisher_admin

    admin_cls.list_display += ('datepublisher_admin',)

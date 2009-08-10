"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the default
views and the template tags.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


def format_date(d, if_none=''):
    """
    Format a date in a nice human readable way: Omit the year if it's the current
    year. Also return a default value if no date is passed in.
    """

    if d is None: return if_none

    now = datetime.now()
    fmt = (d.year == now.year) and '%d.%m' or '%d.%m.%Y'
    return d.strftime(fmt)



def register(cls, admin_cls):
    cls.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=datetime.now))
    cls.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True,
        help_text=_('Leave empty if the entry should stay active forever.')))

    cls.objects.active_filters.append(
            Q(publication_date__lte=datetime.now) & \
            (Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=datetime.now)))

    def datepublisher_admin(self, page):
        return u'%s &ndash; %s' % (
            format_date(page.publication_date),
            format_date(page.publication_end_date, '&infin;'),
            )
    datepublisher_admin.allow_tags = True
    datepublisher_admin.short_description = _('visible from - to')

    admin_cls.datepublisher_admin = datepublisher_admin
    admin_cls.list_display.insert(admin_cls.list_display.index('is_visible_admin') + 1,
                                  'datepublisher_admin')

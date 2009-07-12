"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the default
views and the template tags.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


def register(cls, admin_cls):
    cls.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=datetime.now))
    cls.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True))

    cls.objects.active_filters.append(
            Q(publication_date__lte=datetime.now) & \
            (Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=datetime.now)))

    def is_visible_admin(self, page):
        from feincms.module import django_boolean_icon

        now = datetime.now()

        visible           = page.active
        already_published = page.publication_date <= now
        not_expired       = (page.publication_end_date is None or page.publication_end_date > now)

        format_args = {
            'icon': django_boolean_icon(visible and already_published and not_expired),
            'from': page.publication_date.strftime('%d.%m.%y'),
            'to': page.publication_end_date and page.publication_end_date.strftime('%d.%m.%y') or '&infin;',
            }

        reason = (not visible and _('%(icon)s (not active)')) or \
                 (not already_published and _('%(icon)s (until %(from)s)')) or \
                 (not not_expired and _('%(icon)s (since %(to)s)')) or \
                 _('%(icon)s (%(from)s &ndash; %(to)s)')
        return reason % format_args

    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('is visible')

    admin_cls.is_visible_admin = is_visible_admin
    admin_cls.list_display[admin_cls.list_display.index('active')] = 'is_visible_admin'

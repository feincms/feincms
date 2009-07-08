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
            Q(publication_date__lte=datetime.now) and \
            (Q(publication_end_date__isnull=True) or Q(publication_end_date__gt=datetime.now)))

    def _boolean_icon(field_val, alt_text=None):
        # Origin: contrib/admin/templatetags/admin_list.py
        BOOLEAN_MAPPING = { True: 'yes', False: 'no', None: 'unknown' }
        return (u'<img src="%simg/admin/icon-%s.gif" alt="%s" title="%s" />' % 
                (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], alt_text, alt_text))

    def is_visible_admin(self, page):
        now = datetime.now()

        visible           = page.active
        already_published = page.publication_date <= now
        not_expired       = (page.publication_end_date is None or page.publication_end_date > now)

        reason = (not visible and _('Page not active')) or \
                 (not already_published and _('Page not yet published')) or \
                 (not not_expired and _('Page expired')) or \
                 _('Page visible')
        return _boolean_icon(visible and already_published and not_expired, reason)

    is_visible_admin.allow_tags = True
    is_visible_admin.short_description = _('visible')
    
    admin_cls.is_visible_admin = is_visible_admin

    def datepublisher_admin(self, page):
        if not page.active:
            return _('Not active')

        if page.publication_end_date:
            return u'%s &ndash; %s' % (
                page.publication_date.strftime('%d.%m.%Y'),
                page.publication_end_date.strftime('%d.%m.%Y'),
                )

        return u'%s &ndash; &infin;' % (
            page.publication_date.strftime('%d.%m.%Y'),
            )

    datepublisher_admin.allow_tags = True
    datepublisher_admin.short_description = _('publish dates')
    admin_cls.datepublisher_admin = datepublisher_admin

    admin_cls.list_display.extend(('is_visible_admin', 'datepublisher_admin'))

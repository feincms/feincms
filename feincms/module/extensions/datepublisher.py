"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the
default views and the template tags.

Depends on the page class having a "active_filters" list that will be used by
the page's manager to determine which entries are to be considered active.
"""
# ------------------------------------------------------------------------

from __future__ import absolute_import, unicode_literals

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.cache import patch_response_headers
from django.utils.translation import ugettext_lazy as _

from feincms import extensions


# ------------------------------------------------------------------------
def format_date(d, if_none=''):
    """
    Format a date in a nice human readable way: Omit the year if it's the
    current year. Also return a default value if no date is passed in.
    """

    if d is None:
        return if_none

    now = timezone.now()
    fmt = (d.year == now.year) and '%d.%m' or '%d.%m.%Y'
    return d.strftime(fmt)


def latest_children(self):
    return self.get_children().order_by('-publication_date')


# ------------------------------------------------------------------------
def granular_now(n=None):
    """
    A datetime.now look-alike that returns times rounded to a five minute
    boundary. This helps the backend database to optimize/reuse/cache its
    queries by not creating a brand new query each time.

    Also useful if you are using johnny-cache or a similar queryset cache.
    """
    if n is None:
        n = timezone.now()
    # WARNING/TODO: make_aware can raise a pytz NonExistentTimeError or
    # AmbiguousTimeError if the resultant time is invalid in n.tzinfo
    # -- see https://github.com/feincms/feincms/commit/5d0363df
    return timezone.make_aware(
        datetime(n.year, n.month, n.day, n.hour, (n.minute // 5) * 5),
        n.tzinfo)


# ------------------------------------------------------------------------
def datepublisher_response_processor(page, request, response):
    """
    This response processor is automatically added when the datepublisher
    extension is registered. It sets the response headers to match with
    the publication end date of the page so that upstream caches and
    the django caching middleware know when to expunge the copy.
    """
    expires = page.publication_end_date
    if expires is not None:
        delta = expires - timezone.now()
        delta = int(delta.days * 86400 + delta.seconds)
        patch_response_headers(response, delta)


# ------------------------------------------------------------------------
class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class(
            'publication_date',
            models.DateTimeField(_('publication date'), default=granular_now))
        self.model.add_to_class(
            'publication_end_date',
            models.DateTimeField(
                _('publication end date'),
                blank=True, null=True,
                help_text=_(
                    'Leave empty if the entry should stay active forever.')))
        self.model.add_to_class('latest_children', latest_children)

        # Patch in rounding the pub and pub_end dates on save
        orig_save = self.model.save

        def granular_save(obj, *args, **kwargs):
            if obj.publication_date:
                obj.publication_date = granular_now(obj.publication_date)
            if obj.publication_end_date:
                obj.publication_end_date = granular_now(
                    obj.publication_end_date)
            orig_save(obj, *args, **kwargs)
        self.model.save = granular_save

        # Append publication date active check
        if hasattr(self.model._default_manager, 'add_to_active_filters'):
            self.model._default_manager.add_to_active_filters(
                lambda queryset: queryset.filter(
                    Q(publication_date__lte=granular_now()) &
                     (Q(publication_end_date__isnull=True) |
                      Q(publication_end_date__gt=granular_now()))),
                key='datepublisher',
            )

        # Processor to patch up response headers for expiry date
        self.model.register_response_processor(
            datepublisher_response_processor)

    def handle_modeladmin(self, modeladmin):
        def datepublisher_admin(self, obj):
            return '%s &ndash; %s' % (
                format_date(obj.publication_date),
                format_date(obj.publication_end_date, '&infin;'),
            )
        datepublisher_admin.allow_tags = True
        datepublisher_admin.short_description = _('visible from - to')

        modeladmin.__class__.datepublisher_admin = datepublisher_admin

        try:
            pos = modeladmin.list_display.index('is_visible_admin')
        except ValueError:
            pos = len(modeladmin.list_display)

        modeladmin.list_display.insert(pos + 1, 'datepublisher_admin')

        modeladmin.add_extension_options(_('Date-based publishing'), {
            'fields': ['publication_date', 'publication_end_date'],
        })

# ------------------------------------------------------------------------

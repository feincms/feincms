"""
Allows setting a date range for when the page is active. Modifies the active()
manager method so that only pages inside the given range are used in the default
views and the template tags.

Depends on the page class having a "active_filters" list that will be used by
the page's manager to determine which entries are to be considered active.
"""
# ------------------------------------------------------------------------

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

# ------------------------------------------------------------------------
def format_date(d, if_none=''):
    """
    Format a date in a nice human readable way: Omit the year if it's the current
    year. Also return a default value if no date is passed in.
    """

    if d is None: return if_none

    now = datetime.now()
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
        n = datetime.now()
    return datetime(n.year, n.month, n.day, n.hour, (n.minute // 5) * 5)

# ------------------------------------------------------------------------
def register(cls, admin_cls):
    cls.add_to_class('publication_date', models.DateTimeField(_('publication date'),
        default=granular_now))
    cls.add_to_class('publication_end_date', models.DateTimeField(_('publication end date'),
        blank=True, null=True,
        help_text=_('Leave empty if the entry should stay active forever.')))
    cls.add_to_class('latest_children', latest_children)

    # Patch in rounding the pub and pub_end dates on save
    orig_save = cls.save

    def granular_save(obj, *args, **kwargs):
        if obj.publication_date:
            obj.publication_date = granular_now(obj.publication_date)
        if obj.publication_end_date:
            obj.publication_end_date = granular_now(obj.publication_end_date)
        orig_save(obj, *args, **kwargs)
    cls.save = granular_save

    # Append publication date active check
    if hasattr(cls.objects, 'add_to_active_filters'):
        cls.objects.add_to_active_filters(
            Q(publication_date__lte=granular_now) &
            (Q(publication_end_date__isnull=True) | Q(publication_end_date__gt=granular_now)),
            key='datepublisher')

    def datepublisher_admin(self, page):
        return u'%s &ndash; %s' % (
            format_date(page.publication_date),
            format_date(page.publication_end_date, '&infin;'),
            )
    datepublisher_admin.allow_tags = True
    datepublisher_admin.short_description = _('visible from - to')

    admin_cls.datepublisher_admin = datepublisher_admin
    try:
        pos = admin_cls.list_display.index('is_visible_admin')
    except ValueError:
        pos = len(admin_cls.list_display)

    admin_cls.list_display.insert(pos + 1, 'datepublisher_admin')

    admin_cls.add_extension_options(_('Date-based publishing'), {
                'fields': ('publication_date', 'publication_end_date'),
        })

# ------------------------------------------------------------------------

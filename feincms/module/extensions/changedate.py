# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
Track the modification date for pages.
"""

from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

def pre_save_handler(sender, instance, **kwargs):
    """
    Intercept attempts to save and insert the current date and time into
    creation and modification date fields.
    """
    from datetime import datetime

    now = datetime.now()
    if instance.id is None:
        instance.creation_date = now
    instance.modification_date = now

# ------------------------------------------------------------------------
def dt_to_utc_timestamp(dt):
    from time import mktime, gmtime
    return mktime(gmtime(mktime(dt.utctimetuple())))

def register(cls, admin_cls):
    cls.add_to_class('creation_date',     models.DateTimeField(_('creation date'),     null=True, editable=False))
    cls.add_to_class('modification_date', models.DateTimeField(_('modification date'), null=True, editable=False))

    if hasattr(cls, 'cache_key_components'):
        cls.cache_key_components.append(lambda page: page.modification_date and page.modification_date.strftime('%s'))

    if hasattr(cls, 'last_modified'):
        cls.last_modified = lambda p: dt_to_utc_dt(p.modification_date)

    pre_save.connect(pre_save_handler, sender=cls)

# ------------------------------------------------------------------------
def last_modified_response_processor(self, request, response):
    from django.utils.http import http_date

    # Don't include Last-Modified if we don't want to be cached
    if "no-cache" in response.get('Cache-Control', ''):
        return

    # If we already have a Last-Modified, take the later one
    from email.utils import parsedate_tz, mktime_tz

    last_modified = [ dt_to_utc_timestamp(self.modification_date) ]
    if response.has_header('Last-Modified'):
        last_modified.append(mktime_tz(parsedate_tz(response['Last-Modified'])))

    response['Last-Modified'] = http_date(max(last_modified))

# ------------------------------------------------------------------------

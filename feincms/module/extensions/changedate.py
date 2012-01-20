# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
"""
Track the modification date for objects.
"""

try:
    from email.utils import parsedate_tz, mktime_tz
except ImportError: # py 2.4 compat
    from email.Utils import parsedate_tz, mktime_tz

from django.db import models
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

# ------------------------------------------------------------------------
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
    from time import mktime
    return int(mktime(dt.timetuple()))

def register(cls, admin_cls):
    cls.add_to_class('creation_date',     models.DateTimeField(_('creation date'),     null=True, editable=False))
    cls.add_to_class('modification_date', models.DateTimeField(_('modification date'), null=True, editable=False))

    if hasattr(cls, 'cache_key_components'):
        cls.cache_key_components.append(lambda page: page.modification_date and str(dt_to_utc_timestamp(page.modification_date)))

    cls.last_modified = lambda p: p.modification_date

    pre_save.connect(pre_save_handler, sender=cls)

# ------------------------------------------------------------------------
def last_modified_response_processor(page, request, response):
    from django.utils.http import http_date

    # Don't include Last-Modified if we don't want to be cached
    if "no-cache" in response.get('Cache-Control', ''):
        return

    # If we already have a Last-Modified, take the later one
    last_modified = dt_to_utc_timestamp(page.last_modified())
    if response.has_header('Last-Modified'):
        last_modified = max(last_modified, mktime_tz(parsedate_tz(response['Last-Modified'])))

    response['Last-Modified'] = http_date(last_modified)

# ------------------------------------------------------------------------

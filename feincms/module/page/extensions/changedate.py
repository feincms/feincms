"""
Track the modification date for pages.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


def register(cls, admin_cls):
    cls.add_to_class('creation_date', models.DateTimeField(_('creation date'), editable=False))
    cls.add_to_class('modification_date', models.DateTimeField(_('modification date'), editable=False))

    orig_save = cls.save
    def save(page):
        now = datetime.now()
        if page.id is None:
            page.creation_date = now
        page.modification_date = now
        orig_save(page)

    cls.save = save
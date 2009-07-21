"""
Track the modification date for pages.
"""

from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models.signals import pre_save

from feincms.module.page.models import Page

def pre_save_handler(sender, instance, **kwargs):
    """
    Intercept attempts to save and insert the current date and time into
    creation and modification date fields.
    """
    now = datetime.now()
    if instance.id is None:
        instance.creation_date = now
    instance.modification_date = now

def register(cls, admin_cls):
    cls.add_to_class('creation_date',     models.DateTimeField(_('creation date'),     editable=False))
    cls.add_to_class('modification_date', models.DateTimeField(_('modification date'), editable=False))

    pre_save.connect(pre_save_handler, sender=cls)
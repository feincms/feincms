# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  ct_tracker.py
#  Fein
#
#  Created by Martin J. Laubach on 02.10.09.
#  Copyright (c) 2009 Martin J. Laubach. All rights reserved.
#
# ------------------------------------------------------------------------

"""
Track the content types for pages. Instead of gathering the content
types present in each page at run time, save the current state at
saving time, thus saving a db query on page delivery.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_save
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _

# ------------------------------------------------------------------------
def page_count_content_types(self):
    """
    Returns a representation of all the content types present on a page.
    Note that the content types are stored as the id of the django_content_type
    so that it does not depend on the order/number of registered CTs.
    """
    ct_inventory = {}

    if self.id is not None:
        # find all concrete content type tables which have at least one entry for
        # the current CMS object
        sql = ' UNION '.join([
            'SELECT %d AS ct_idx, region, COUNT(*) FROM %s WHERE parent_id=%s GROUP BY region' % (
                idx,
                cls._meta.db_table,
                self.pk) for idx, cls in enumerate(self._feincms_content_types)])

        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(sql)

        row = cursor.fetchall()

        # Now convert the content types to django ContentType.id, so the result
        # set is stable wrt. registered feincms content types.
        for ct_idx, region, count in row:
            from django.contrib.contenttypes.models import ContentType

            if count:
                if not ct_inventory.has_key(region):
                    ct_inventory[region] = []
                ct_inventory[region].append(ContentType.objects.get_for_model(self._feincms_content_types[ct_idx]).id)

    return ct_inventory

# ------------------------------------------------------------------------
def page_get_content_types_for_region(self, region):
    """
    Overrides Page.get_content_types_for_region.
    """

    # Prime translation map and cache it in the class. This needs to be
    # done late as opposed to at class definition time as not all information
    # is ready, especially when we are doing a "syncdb" the ContentType table
    # does not yet exist
    tr_map = getattr(self.__class__, '_django_ct_to_feincms_ct_map', None)
    if tr_map is None:
        tr_map = { }
        for idx, ct in enumerate(self._feincms_content_types):
            tr_map[ContentType.objects.get_for_model(ct).id] = idx
        setattr(self.__class__, '_django_ct_to_feincms_ct_map', tr_map)

    inv = simplejson.loads(self._ct_inventory)

    retval = [0] * len(self._feincms_content_types)
    region_ct_inventory = inv.get(region.key, [])
    for django_ct in region_ct_inventory:
        retval[tr_map[django_ct]] = 1
    
    return retval

# ------------------------------------------------------------------------
def pre_save_handler(sender, instance, **kwargs):
    """
    Intercept save and store the currently used content types into the page itself.
    """
    ct_inventory = instance.count_content_types()
    instance._ct_inventory = simplejson.dumps(ct_inventory)

# ------------------------------------------------------------------------
def register(cls, admin_cls):
    cls.add_to_class('_ct_inventory', models.CharField(_('content types'), max_length=500, editable=False))
    cls.add_to_class('count_content_types', page_count_content_types)

    cls.orig_get_content_types_for_region = cls._get_content_types_for_region
    cls._get_content_types_for_region = page_get_content_types_for_region

    pre_save.connect(pre_save_handler, sender=cls)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------

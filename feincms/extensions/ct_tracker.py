# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  ct_tracker.py
#  FeinCMS
#
#  Created by Martin J. Laubach on 02.10.09.
#  Copyright (c) 2009 Martin J. Laubach. All rights reserved.
#  Updated in 2011 by Matthias Kestenholz for the 1.3 release.
#
# ------------------------------------------------------------------------

"""
Track the content types for pages. Instead of gathering the content
types present in each page at run time, save the current state at
saving time, thus saving at least one DB query on page delivery.
"""

from __future__ import absolute_import, unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import class_prepared, post_save, pre_save
from django.utils.translation import ugettext_lazy as _

from feincms import extensions
from feincms.contrib.fields import JSONField
from feincms.models import ContentProxy


INVENTORY_VERSION = 1
_translation_map_cache = {}


# ------------------------------------------------------------------------
class TrackerContentProxy(ContentProxy):
    def _fetch_content_type_counts(self):
        """
        If an object with an empty _ct_inventory is encountered, compute all
        the content types currently used on that object and save the list in
        the object itself. Further requests for that object can then access
        that information and find out which content types are used without
        resorting to multiple selects on different ct tables.

        It is therefore important that even an "empty" object does not have an
        empty _ct_inventory.
        """

        if 'counts' not in self._cache:
            if (self.item._ct_inventory and
                    self.item._ct_inventory.get('_version_', -1) ==
                    INVENTORY_VERSION):

                try:
                    self._cache['counts'] = self._from_inventory(
                        self.item._ct_inventory)
                except KeyError:
                    # It's possible that the inventory does not fit together
                    # with the current models anymore, f.e. because a content
                    # type has been removed.
                    pass

            if 'counts' not in self._cache:
                super(TrackerContentProxy, self)._fetch_content_type_counts()

                self.item._ct_inventory = self._to_inventory(
                    self._cache['counts'])

                self.item.__class__.objects.filter(id=self.item.id).update(
                    _ct_inventory=self.item._ct_inventory)

                # Run post save handler by hand
                if hasattr(self.item, 'get_descendants'):
                    self.item.get_descendants(include_self=False).update(
                        _ct_inventory=None)
        return self._cache['counts']

    def _translation_map(self):
        cls = self.item.__class__
        if cls not in _translation_map_cache:
            # Prime translation map and cache it in the class. This needs to be
            # done late as opposed to at class definition time as not all
            # information is ready, especially when we are doing a "syncdb" the
            # ContentType table does not yet exist
            map = {}
            for idx, fct in enumerate(self.item._feincms_content_types):
                dct = ContentType.objects.get_for_model(fct)

                # Rely on non-negative primary keys
                map[-dct.id] = idx  # From-inventory map
                map[idx] = dct.id  # To-inventory map

            _translation_map_cache[cls] = map
        return _translation_map_cache[cls]

    def _from_inventory(self, inventory):
        """
        Transforms the inventory from Django's content types to FeinCMS's
        ContentProxy counts format.
        """

        map = self._translation_map()

        return dict((region, [
            (pk, map[-ct]) for pk, ct in items
        ]) for region, items in inventory.items() if region != '_version_')

    def _to_inventory(self, counts):
        map = self._translation_map()

        inventory = dict(
            (
                region,
                [(pk, map[ct]) for pk, ct in items],
            ) for region, items in counts.items()
        )
        inventory['_version_'] = INVENTORY_VERSION
        return inventory


# ------------------------------------------------------------------------
def class_prepared_handler(sender, **kwargs):
    # It might happen under rare circumstances that not all model classes
    # are fully loaded and initialized when the translation map is accessed.
    # This leads to (lots of) crashes on the server. Better be safe and
    # kill the translation map when any class_prepared signal is received.
    _translation_map_cache.clear()


class_prepared.connect(class_prepared_handler)


# ------------------------------------------------------------------------
def tree_post_save_handler(sender, instance, **kwargs):
    """
    Clobber the _ct_inventory attribute of this object and all sub-objects
    on save.
    """
    # TODO: Does not find everything it should when ContentProxy content
    # inheritance has been customized.
    instance.get_descendants(include_self=True).update(_ct_inventory=None)


# ------------------------------------------------------------------------
def single_pre_save_handler(sender, instance, **kwargs):
    """Clobber the _ct_inventory attribute of this object"""

    instance._ct_inventory = None


# ------------------------------------------------------------------------
class Extension(extensions.Extension):
    def handle_model(self):
        self.model.add_to_class('_ct_inventory', JSONField(
            _('content types'), editable=False, blank=True, null=True))
        self.model.content_proxy_class = TrackerContentProxy

        pre_save.connect(single_pre_save_handler, sender=self.model)
        if hasattr(self.model, 'get_descendants'):
            post_save.connect(tree_post_save_handler, sender=self.model)

# ------------------------------------------------------------------------

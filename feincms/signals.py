# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 2011-08-01 
#  Copyright (c) 2011 Martin J. Laubach. All rights reserved.
#
# ------------------------------------------------------------------------

from django.dispatch import Signal

# ------------------------------------------------------------------------
# This signal is sent when an item editor managed object is completely
# saved, especially including all foreign or manytomany dependencies.

itemeditor_post_save_related = Signal(providing_args=["instance", "created"])

# ------------------------------------------------------------------------

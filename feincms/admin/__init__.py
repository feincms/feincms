# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
#
#  Created by Martin J. Laubach on 2011-11-11
#  Copyright (c) 2011 Martin J. Laubach. All rights reserved.
#
# ------------------------------------------------------------------------

def add_extension_options(admin_cls, *fieldset):
    """
    Convenience wrapper to add an extension's fields
    to an admin class, with special consideration to
    feincms.Page -- it sports a supporting method
    that takes care to nicely sort and format things.
    """

    fieldset[1]['classes'] = list(fieldset[1].get('classes', []))
    fieldset[1]['classes'].extend(['feincms-collapse'])

    if hasattr(admin_cls, 'add_extension_options'):
        admin_cls.add_extension_options(*fieldset)
    else:
        if isinstance(admin_cls.fieldsets, tuple):
            admin_cls.fieldsets = list(admin_cls.fieldsets)
        admin_cls.fieldsets.append(fieldset)

# ------------------------------------------------------------------------

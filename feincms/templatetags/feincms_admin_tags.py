from __future__ import absolute_import, unicode_literals

import django
from django import template


register = template.Library()


@register.filter
def post_process_fieldsets(fieldset):
    """
    Removes a few fields from FeinCMS admin inlines, those being
    ``id``, ``DELETE`` and ``ORDER`` currently.

    Additionally, it ensures that dynamically added fields (i.e.
    ``ApplicationContent``'s ``admin_fields`` option) are shown.
    """
    # abort if fieldset is customized
    if fieldset.model_admin.fieldsets:
        return fieldset

    fields_to_include = set(fieldset.form.fields.keys())
    for f in ('id', 'DELETE', 'ORDER'):
        fields_to_include.discard(f)

    def _filter_recursive(fields):
        ret = []
        for f in fields:
            if isinstance(f, (list, tuple)):
                # Several fields on one line
                sub = _filter_recursive(f)
                # Only add if there's at least one field left
                if sub:
                    ret.append(sub)
            elif f in fields_to_include:
                ret.append(f)
                fields_to_include.discard(f)
        return ret

    new_fields = _filter_recursive(fieldset.fields)
    # Add all other fields (ApplicationContent's admin_fields) to
    # the end of the fieldset
    for f in fields_to_include:
        new_fields.append(f)

    fieldset.fields = new_fields
    return fieldset


@register.assignment_tag
def is_popup_var():
    """
    Django 1.6 requires _popup=1 for raw id field popups, earlier versions
    require pop=1.

    The explicit version check is a bit ugly, but works well.

    (Wrong parameters aren't simply ignored by django.contrib.admin, the
    change list actively errors out by redirecting to ?e=1)
    """
    if django.VERSION < (1, 6):
        return 'pop=1'
    return '_popup=1'

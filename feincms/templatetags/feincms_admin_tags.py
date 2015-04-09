from __future__ import absolute_import, unicode_literals

import warnings

from django import template
from django.contrib.auth import get_permission_codename


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
    warnings.warn(
        'Hardcode _popup=1 instead of using is_popup_var.',
        DeprecationWarning, stacklevel=2)

    return '_popup=1'


@register.inclusion_tag('admin/feincms/content_type_selection_widget.html',
                        takes_context=True)
def show_content_type_selection_widget(context, region):
    """
    {% show_content_type_selection_widget region %}
    """
    if 'request' in context:
        user = context['request'].user
    elif 'user' in context:
        user = context['user']
    else:
        user = None

    grouped = {}
    ungrouped = []

    if user:
        for ct in region._content_types:
            # Skip cts that we shouldn't be adding anyway
            opts = ct._meta
            perm = opts.app_label + "." + get_permission_codename('add', opts)
            if not user.has_perm(perm):
                continue

            ct_info = (ct.__name__.lower(), ct._meta.verbose_name)
            if hasattr(ct, 'optgroup'):
                if ct.optgroup in grouped:
                    grouped[ct.optgroup].append(ct_info)
                else:
                    grouped[ct.optgroup] = [ct_info]
            else:
                ungrouped.append(ct_info)

    return {'grouped': grouped, 'ungrouped': ungrouped}

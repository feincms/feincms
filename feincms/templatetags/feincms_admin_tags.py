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

    fields_to_include = set(fieldset.form.fields.keys())
    for f in ('id', 'DELETE', 'ORDER'):
        fields_to_include.discard(f)

    def _filter_recursive(fields):
        ret = []
        for f in fields:
            if hasattr(f, '__iter__'):
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

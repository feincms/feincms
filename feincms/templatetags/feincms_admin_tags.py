from django import template


register = template.Library()


@register.filter
def post_process_fieldsets(fieldset):
    formset = getattr(fieldset, 'formset', None)

    if formset: # Only apply special handling in formsets
        # Determine whether the given formset works on a FeinCMS inline
        try:
            content_types = fieldset.model_admin.model._feincms_content_types
            model = formset.form._meta.model

            process = model in content_types
        except AttributeError:
            process = False

        if process:
            # Exclude special fields and the primary key
            excluded_fields = ('id', 'DELETE', 'ORDER')
            fieldset.fields = [f for f in fieldset.form.fields.keys() if f not in excluded_fields]

    for line in fieldset:
        yield line

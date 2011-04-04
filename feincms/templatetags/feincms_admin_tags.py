from django import template


register = template.Library()


@register.filter
def post_process_fieldsets(fieldset):
    """
    Removes a few fields from FeinCMS admin inlines, those being
    ``id``, ``DELETE`` and ``ORDER`` currently.
    """

    process = fieldset.model_admin.verbose_name_plural.startswith('Feincms_Inline:')
    if process:
        # Exclude special fields and the primary key
        excluded_fields = ('id', 'DELETE', 'ORDER')
        fieldset.fields = [f for f in fieldset.form.fields.keys() if f not in excluded_fields]

    for line in fieldset:
        yield line

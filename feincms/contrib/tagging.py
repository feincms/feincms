# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
# FeinCMS django-tagging support. To add tagging to your (page) model,
# simply do a
#
#    from feincms.contrib import tagging
#    tagging.tag_model(Page)
# ------------------------------------------------------------------------

from django.db.models.signals import pre_save

# ------------------------------------------------------------------------
def pre_save_handler(sender, instance, **kwargs):
    """
    Intercept attempts to save and sort the tag field alphabetically, so
    we won't have different permutations in the filter list.
    """
    from ..tagging.utils import parse_tag_input

    taglist = parse_tag_input(instance.tags)
    if len(taglist) > 1:
        taglist.sort()
        instance.tags = ','.join(taglist)
    elif len(taglist) == 0:
        instance.tags = ''

# ------------------------------------------------------------------------
def tag_model(cls, admin_cls=None, field_name='tags', sort_tags=False):
    """
    tag_model accepts a number of named parameters:
    
    admin_cls   If set to a subclass of ModelAdmin, will insert the tag
                field into the list_display and list_filter fields.
    field_name  Defaults to "tags", can be used to name your tag field
                differently.
    sort_tags   Boolean, defaults to False. If set to True, a pre_save
                handler will be inserted to sort the tag field alphabetically.
                This is useful in case you want a canonical representation
                for a tag collection, as when you're presenting a list of
                tag combinations (e.g. in an admin filter list).
    """
    from ..tagging.fields import TagField
    from ..tagging import register as tagging_register

    cls.add_to_class(field_name, TagField(field_name.capitalize(), blank=True))
    # use another name for the tag descriptor
    # See http://code.google.com/p/django-tagging/issues/detail?id=95 for the reason why
    tagging_register(cls, tag_descriptor_attr='tagging_' + field_name)

    if admin_cls:
        admin_cls.list_display.append(field_name)
        admin_cls.list_filter.append(field_name)

    if sort_tags:
        pre_save.connect(pre_save_handler, sender=cls)

# ------------------------------------------------------------------------

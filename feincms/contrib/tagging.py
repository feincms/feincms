# ------------------------------------------------------------------------
# coding=utf-8
# ------------------------------------------------------------------------
# FeinCMS django-tagging support. To add tagging to your (page) model,
# simply do a
#
#    from feincms.contrib import tagging
#    tagging.tag_model(Page)
# ------------------------------------------------------------------------

from __future__ import absolute_import

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField

# ------------------------------------------------------------------------
def taglist_to_string(taglist):
    retval = ''
    if len(taglist) >= 1:
        taglist.sort()
        retval = ','.join(taglist)
    return retval

# ------------------------------------------------------------------------
# The following is lifted from:
# http://code.google.com/p/django-tagging/issues/detail?id=189

"""
TagSelectField

A variation of the django-tagging TagField which uses a
SelectMultiple widget instead of free text field.

class MyModel(models.Model):
    ...
    tags = TagSelectField(filter_horizontal=True, blank=False)

"""

class TagSelectFormField(forms.MultipleChoiceField):
    def clean(self, value):
        return taglist_to_string(list(value))

class TagSelectField(TagField):
    def __init__(self, filter_horizontal=False, *args, **kwargs):
        super(TagSelectField, self).__init__(*args, **kwargs)
        self.filter_horizontal = filter_horizontal

    def formfield(self, **defaults):
        from tagging.models import Tag
        from tagging.utils import parse_tag_input

        if self.filter_horizontal:
            widget = FilteredSelectMultiple(self.verbose_name, is_stacked=False)
        else:
            widget = forms.SelectMultiple()

        def _render(name, value, attrs=None, *args, **kwargs):
            value = parse_tag_input(value)
            return type(widget).render(widget, name, value, attrs, *args, **kwargs)
        widget.render = _render
        defaults['widget'] = widget
        choices = [ (str(t), str(t)) for t in Tag.objects.all() ]
        return TagSelectFormField(choices=choices, required=not self.blank, **defaults)

# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
def pre_save_handler(sender, instance, **kwargs):
    """
    Intercept attempts to save and sort the tag field alphabetically, so
    we won't have different permutations in the filter list.
    """
    from tagging.utils import parse_tag_input

    taglist = parse_tag_input(instance.tags)
    instance.tags = taglist_to_string(taglist)

# ------------------------------------------------------------------------
def tag_model(cls, admin_cls=None, field_name='tags', sort_tags=False, select_field=False, auto_add_admin_field=True):
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
    select_field If True, show a multi select instead of the standard
                CharField for tag entry.
    auto_add_admin_field If True, attempts to add the tag field to the admin
                class.
    """
    from tagging import register as tagging_register

    cls.add_to_class(field_name, (select_field and TagSelectField or TagField)(field_name.capitalize(), blank=True))
    # use another name for the tag descriptor
    # See http://code.google.com/p/django-tagging/issues/detail?id=95 for the reason why
    tagging_register(cls, tag_descriptor_attr='tagging_' + field_name)

    if admin_cls:
        admin_cls.list_display.append(field_name)
        admin_cls.list_filter.append(field_name)

        if auto_add_admin_field and hasattr(admin_cls, 'add_extension_options'):
            admin_cls.add_extension_options(_('Tagging'), {
                'fields': (field_name,)
            })

    if sort_tags:
        pre_save.connect(pre_save_handler, sender=cls)

# ------------------------------------------------------------------------

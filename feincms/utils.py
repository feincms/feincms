"""
Usage instructions

Prefilled attributes
====================

The two functions prefilled_attribute and prefill_entry_list help you avoid
massive amounts of database queries when displaying a list of CMS items with
content objects. This is especially useful if f.e. your blog content is derived
from FeinCMS and you want to show a list of recent blog entries.

Example:

    from feincms.content.image.models import ImageContent
    from feincms.content.richtext.models import RichTextContent
    from feincms.models import Base
    from feincms.utils import prefilled_attribute, prefill_entry_list

    class Author(models.Model):
        # ...

    class Entry(Base):
        authors = models.ManyToManyField

        author_list = prefilled_attr('authors')
        richtexts = prefilled_attr('richtextcontent_set')
        images = prefilled_attr('imagecontent_set')

    Entry.create_content_type(RichTextContent)
    Entry.create_content_type(ImageContent)


    Then, inside your view function or inside a template tag, call
    prefill_entry_list with the attribute names:

    prefill_entry_list(queryset, 'authors', 'richtextcontent_set', 'imagecontent_set')

    or

    {% load feincms_tags %}
    {% feincms_prefill_entry_list object_list "authors,richtextcontent_set,imagecontent_set" %}
"""

from django.db import connection, models
from django.db.models.fields import related


def get_object(path, fail_silently=False):
    dot = path.rindex('.')
    try:
        return getattr(__import__(path[:dot], {}, {}, ['']), path[dot + 1:])
    except (ImportError, AttributeError):
        if not fail_silently:
            raise

    return None


def prefilled_attribute(name):
    key = '_prefill_%s' % name

    def _prop(self):
        if not hasattr(self, key):
            setattr(self, key, list(getattr(self, name).all()))

        return getattr(self, key)

    return property(_prop)


def collect_dict_values(data):
    dic = {}
    for key, value in data:
        dic.setdefault(key, []).append(value)
    return dic


def prefill_entry_list(queryset, *attrs):
    queryset = list(queryset)

    if not queryset:
        return queryset

    arbitrary = queryset[0]
    cls = arbitrary.__class__

    from_fk = []
    from_m2m = []

    for attr in attrs:
        related_model = getattr(arbitrary, attr).model
        descriptor = getattr(cls, attr)

        if isinstance(descriptor, related.ReverseManyRelatedObjectsDescriptor):
            f = arbitrary._meta.get_field(attr)
            qn = connection.ops.quote_name

            sql = 'SELECT DISTINCT %s, %s FROM %s WHERE %s in (%s)' % (
                qn(f.m2m_column_name()),
                qn(f.m2m_reverse_name()),
                qn(f.m2m_db_table()),
                qn(f.m2m_column_name()),
                ', '.join(['%s'] * len(queryset)))

            cursor = connection.cursor()
            cursor.execute(sql, [entry.id for entry in queryset])
            mapping = cursor.fetchall()

            related_objects = dict((o.id, o) for o in related_model.objects.all())

            assigned_objects = {}

            for entry, obj_id in mapping:
                assigned_objects.setdefault(entry, set()).add(related_objects[obj_id])

            from_m2m.append((attr, assigned_objects))
        else:
            from_fk.append((attr,
                collect_dict_values((o.parent_id, o) for o in related_model.objects.filter(
                    parent__in=queryset).select_related('parent', 'region'))))

    for entry in queryset:
        for attr, dic in from_fk:
            setattr(entry, '_prefill_%s' % attr, dic.get(entry.id, []))
        for attr, dic in from_m2m:
            setattr(entry, '_prefill_%s' % attr, dic.get(entry.id, []))

    return queryset


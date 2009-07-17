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
    """
    Prefill a queryset with related data. Instead of querying the related tables
    over and over for every single entry of the queryset, the absolute minimum of
    queries is performed per related field, one for reverse foreign keys, two for
    many to many fields. The returned data is assigned to the individual entries
    afterwards, where it can be made easily accessible by using the
    prefilled_attribute property generator above.
    """

    # Evaluate queryset. We need a list of objects, because we need to iterate over
    # to find out
    queryset = list(queryset)

    if not queryset:
        return queryset

    # Get an arbitrary object of the queryset. We need this to determine the field
    # type alter
    arbitrary = queryset[0]
    cls = arbitrary.__class__

    from_fk = []
    from_m2m = []

    for attr in attrs:
        related_model = getattr(arbitrary, attr).model
        descriptor = getattr(cls, attr)

        if isinstance(descriptor, related.ReverseManyRelatedObjectsDescriptor):
            # Process many to many fields
            f = arbitrary._meta.get_field(attr)
            qn = connection.ops.quote_name

            # Query the table linking the two models
            sql = 'SELECT DISTINCT %s, %s FROM %s WHERE %s in (%s)' % (
                qn(f.m2m_column_name()),
                qn(f.m2m_reverse_name()),
                qn(f.m2m_db_table()),
                qn(f.m2m_column_name()),
                ', '.join(['%s'] * len(queryset)))

            cursor = connection.cursor()
            cursor.execute(sql, [entry.id for entry in queryset])
            mapping = cursor.fetchall()

            # Get all related models which are linked with any entry in the queryset
            related_objects = dict((o.id, o) for o in related_model.objects.filter(
                id__in=[v for k, v in mapping]))

            assigned_objects = {}

            for entry, obj_id in mapping:
                assigned_objects.setdefault(entry, set()).add(related_objects[obj_id])

            from_m2m.append((attr, assigned_objects))
        else:
            # Process reverse foreign keys
            from_fk.append((attr,
                collect_dict_values((o.parent_id, o) for o in related_model.objects.filter(
                    parent__in=queryset).select_related('parent', 'region'))))

    # Assign the collected values onto the individual queryset objects
    for entry in queryset:
        for attr, dic in from_fk:
            setattr(entry, '_prefill_%s' % attr, dic.get(entry.id, []))
        for attr, dic in from_m2m:
            setattr(entry, '_prefill_%s' % attr, dic.get(entry.id, []))

    return queryset


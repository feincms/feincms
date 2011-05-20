.. _tools-utils-prefilledattributes:

Prefetching data for a list of objects from the database
========================================================

If you want to display several CMS objects on one site, it can happen quickly
that the number of SQL queries needed to generate the page goes up to intolerable
heights. The same queries are executed over and over for every object in the list.
This section describes how the bundled tools can be used to reduce the amount of
SQL queries needed.

The two functions ``prefilled_attribute`` and ``prefill_entry_list`` help you avoid
massive amounts of database queries when displaying a list of CMS items with
content objects. This is especially useful if f.e. your blog content is derived
from FeinCMS and you want to show a list of recent blog entries.

::

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
``prefill_entry_list`` with the attribute names::

    prefill_entry_list(queryset, 'authors', 'richtextcontent_set', 'imagecontent_set')


If you want to use the prefilled attributes mechanism with generic views, you
cannot use the ``prefill_entry_list`` function when passing the queryset to the
generic view, because the method needs to evaluate the queryset. The earliest
point where you have access to your queryset again is inside the template. The
``feincms_prefill_entry_list`` template tag can be used for the same purpose::

    {% load feincms_tags %}
    {% feincms_prefill_entry_list object_list "authors,richtextcontent_set,imagecontent_set" %}

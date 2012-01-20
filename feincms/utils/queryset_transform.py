# Straight import from https://github.com/simonw/django-queryset-transform

"""
django_queryset_transform
=========================

Allows you to register a transforming map function with a Django QuerySet
that will be executed only when the QuerySet itself has been evaluated.

This allows you to build optimisations like "fetch all tags for these 10 rows"
while still benefiting from Django's lazy QuerySet evaluation.

For example:

    def lookup_tags(item_qs):
        item_pks = [item.pk for item in item_qs]
        m2mfield = Item._meta.get_field_by_name('tags')[0]
        tags_for_item = Tag.objects.filter(
            item__in = item_pks
        ).extra(select = {
            'item_id': '%s.%s' % (
                m2mfield.m2m_db_table(), m2mfield.m2m_column_name()
            )
        })
        tag_dict = {}
        for tag in tags_for_item:
            tag_dict.setdefault(tag.item_id, []).append(tag)
        for item in item_qs:
            item.fetched_tags = tag_dict.get(item.pk, [])

    qs = Item.objects.filter(name__contains = 'e').transform(lookup_tags)

    for item in qs:
        print item, item.fetched_tags

Prints:

    Winter comes to Ogglesbrook [<sledging>, <snow>, <winter>, <skating>]
    Summer now [<skating>, <sunny>]

But only executes two SQL queries - one to fetch the items, and one to fetch ALL of the tags for those items.

Since the transformer function can transform an evaluated QuerySet, it
doesn't need to make extra database calls at all - it should work for things
like looking up additional data from a cache.multi_get() as well.

Originally inspired by http://github.com/lilspikey/django-batch-select/



LICENSE
=======

Copyright (c) 2010, Simon Willison.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from django.db import models

class TransformQuerySet(models.query.QuerySet):
    def __init__(self, *args, **kwargs):
        super(TransformQuerySet, self).__init__(*args, **kwargs)
        self._transform_fns = []

    def _clone(self, klass=None, setup=False, **kw):
        c = super(TransformQuerySet, self)._clone(klass, setup, **kw)
        c._transform_fns = self._transform_fns[:]
        return c

    def transform(self, fn):
        c = self._clone()
        c._transform_fns.append(fn)
        return c

    def iterator(self):
        result_iter = super(TransformQuerySet, self).iterator()
        if self._transform_fns:
            results = list(result_iter)
            for fn in self._transform_fns:
                fn(results)
            return iter(results)
        return result_iter

class TransformManager(models.Manager):

    def get_query_set(self):
        return TransformQuerySet(self.model, using=self._db)

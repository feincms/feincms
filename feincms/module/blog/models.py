"""
This is more a proof-of-concept for your own :class:`feincms.module.Base`
subclasses than a polished or even sufficient blog module implementation.

It does work, though.
"""

from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models import signals
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from feincms import settings
from feincms.admin import item_editor
from feincms.management.checker import check_database_schema
from feincms.models import Base


class EntryManager(models.Manager):
    def published(self):
        return self.filter(
            published=True,
            published_on__isnull=False,
            published_on__lte=timezone.now(),
        )


@python_2_unicode_compatible
class Entry(Base):
    published = models.BooleanField(_('published'), default=False)
    title = models.CharField(
        _('title'), max_length=100,
        help_text=_('This is used for the generated navigation too.'))
    slug = models.SlugField()

    published_on = models.DateTimeField(
        _('published on'), blank=True, null=True,
        help_text=_(
            'Will be set automatically once you tick the `published`'
            ' checkbox above.'))

    class Meta:
        get_latest_by = 'published_on'
        ordering = ['-published_on']
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    objects = EntryManager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.published and not self.published_on:
            self.published_on = timezone.now()
        super(Entry, self).save(*args, **kwargs)
    save.alters_data = True

    @models.permalink
    def get_absolute_url(self):
        return ('blog_entry_detail', (self.id,), {})


if settings.FEINCMS_CHECK_DATABASE_SCHEMA:
    signals.post_syncdb.connect(
        check_database_schema(Entry, __name__),
        weak=False)


class EntryAdmin(item_editor.ItemEditor):
    date_hierarchy = 'published_on'
    list_display = ['__str__', 'published', 'published_on']
    list_filter = ['published']
    search_fields = ['title', 'slug']
    prepopulated_fields = {
        'slug': ('title',),
    }

    raw_id_fields = []

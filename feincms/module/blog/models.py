from datetime import datetime

from django.contrib import admin
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _

from feincms.admin import editor
from feincms.management.checker import check_database_schema
from feincms.models import Base
from feincms.utils import get_object


class EntryManager(models.Manager):
    def published(self):
        return self.filter(
            published__isnull=False,
            published_on__lte=datetime.now(),
            )


class Entry(Base):
    published = models.BooleanField(_('published'), default=False)
    title = models.CharField(_('title'), max_length=100,
        help_text=_('This is used for the generated navigation too.'))
    slug = models.SlugField()

    published_on = models.DateTimeField(_('published on'), blank=True, null=True,
        help_text=_('Will be set automatically once you tick the `published` checkbox above.'))

    class Meta:
        get_latest_by = 'published_on'
        ordering = ['-published_on']
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    objects = EntryManager()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.published and not self.published_on:
            self.published_on = datetime.now()
        super(Entry, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('blog_entry_detail', (self.id,), {})

    @classmethod
    def register_extension(cls, register_fn):
        register_fn(cls, EntryAdmin)


signals.post_syncdb.connect(check_database_schema(Entry, __name__), weak=False)


class EntryAdmin(editor.ItemEditor):
    date_hierarchy = 'published_on'
    list_display = ('__unicode__', 'published', 'published_on')
    list_filter = ('published',)
    search_fields = ('title', 'slug',)
    prepopulated_fields = {
        'slug': ('title',),
        }

    raw_id_fields = []

import time
from datetime import datetime

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

import feedparser


class RSSContent(models.Model):
    """
    RSS feed inclusion content.

    This content requires a cronjob on the server, which runs
    ``./manage.py update_rsscontent`` every couple of hours.
    """

    title = models.CharField(_('title'), max_length=50,
        help_text=_('The rss field is updated several times a day. A change in the title will only be visible on the home page after the next feed update.'))
    link = models.URLField(_('link'))
    rendered_content = models.TextField(_('pre-rendered content'), blank=True, editable=False)
    last_updated = models.DateTimeField(_('last updated'), blank=True, null=True)
    max_items = models.IntegerField(_('max. items'), default=5)

    class Meta:
        abstract = True
        verbose_name = _('RSS feed')
        verbose_name_plural = _('RSS feeds')

    def render(self, **kwargs):
        return mark_safe(self.rendered_content)

    def cache_content(self, date_format=None, save=True):
        feed = feedparser.parse(self.link)
        entries = feed['entries'][:self.max_items]
        if date_format:
            for entry in entries:
                entry.updated = time.strftime(date_format,
                    entry.updated_parsed)

        self.rendered_content = render_to_string('content/rss/content.html', {
            'feed_title': self.title,
            'feed_link': feed['feed']['link'],
            'entries': entries,
            })
        self.last_updated = datetime.now()

        if save:
            self.save()


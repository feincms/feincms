from datetime import datetime

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

import feedparser


class RSSContent(models.Model):
    title = models.CharField(help_text=_('The rss field is updated several times a day. A change in the title will only be visible on the home page after the next feed update.'), max_length=50)
    link = models.URLField(_('link'))
    rendered_content = models.TextField(_('Pre-rendered content'), blank=True, editable=False)
    last_updated = models.DateTimeField(_('Last updated'), blank=True, null=True)
    max_items = models.IntegerField(_('Max. items'), default=5)

    class Meta:
        abstract = True
        verbose_name = _('RSS feed')
        verbose_name_plural = _('RSS feeds')

    def render(self, **kwargs):
        return mark_safe(self.rendered_content)

    def cache_content(self):
        print u"Getting RSS feed at %s" % (self.link,)
        feed = feedparser.parse(self.link)

        print u"Pre-rendering content"
        self.rendered_content = render_to_string('content/rss/content.html', {
            'feed_title': self.title,
            'feed_link': feed['feed']['link'],
            'entries': feed['entries'][:self.max_items],
            })
        self.last_updated = datetime.now()

        self.save()


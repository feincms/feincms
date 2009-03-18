from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string

import feedparser


class RSSContent(models.Model):
    link = models.URLField(_('link'))
    rendered_content = models.TextField(_('Pre-rendered content'), blank=True, editable=False)

    class Meta:
        abstract = True

    def render(self, **kwargs):
        return mark_safe(self.rendered_content)
        #u'<div class="rsscontent"> RSS: <a href="'+self.link+'">'+self.link+'</a></div')

    def cache_content(self):
        print u"Getting RSS feed at %s" % (self.link,)
        feed = feedparser.parse(self.link)

        print u"Pre-rendering content"
        self.rendered_content = render_to_string('rsscontent.html', {
            'feed': feed})

        self.save()

